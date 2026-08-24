import os
from unittest.mock import MagicMock

import pytest
from digital_twin.contracts.dtos.parsed_sensor_log_dto import ParsedSensorLogDto
from digital_twin.contracts.ports.outbound.i_baseline_command_repository import (
    IBaselineCommandRepository,
)
from digital_twin.contracts.ports.outbound.i_sensor_log_parser import ISensorLogParser
from digital_twin.twin_reconstruction.application.reconstruct_twin.raw_factory_data_dto import (
    RawFactoryDataDto,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_mapper import (
    ReconstructTwinMapper,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    ReconstructTwinUseCase,
)
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_sync_status_enum import (
    TwinSyncStatus,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_sensor_parser() -> MagicMock:
    return MagicMock(spec=ISensorLogParser)


@pytest.fixture
def mock_command_repo() -> MagicMock:
    repo = MagicMock(spec=IBaselineCommandRepository)
    repo.save.side_effect = lambda entity: entity
    return repo


@pytest.fixture
def mapper() -> ReconstructTwinMapper:
    return ReconstructTwinMapper()


@pytest.fixture
def usecase(
    mock_sensor_parser: MagicMock,
    mock_command_repo: MagicMock,
    mapper: ReconstructTwinMapper,
) -> ReconstructTwinUseCase:
    return ReconstructTwinUseCase(
        sensor_parser=mock_sensor_parser,
        command_repo=mock_command_repo,
        mapper=mapper,
        default_tolerance=5.0,
    )


@pytest.fixture
def valid_ctx() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=[],
    )


def test_tc_happy_path_reconstruct_twin(
    usecase: ReconstructTwinUseCase,
    mock_sensor_parser: MagicMock,
    mock_command_repo: MagicMock,
    valid_ctx: UserContext,
    tmp_path,
):
    """[TC-정상] 가상 공장 복각 및 정합성 검증 성공 시나리오"""
    fake_log_file = tmp_path / "sensor_sample.csv"
    fake_log_file.write_text("timestamp,deviation\n1,0.5\n2,0.8\n")

    # ParsedSensorLogDto 반환 설정
    mock_sensor_parser.parse.return_value = ParsedSensorLogDto(
        file_name="sensor_sample.csv",
        total_samples=2,
        sampling_rate_hz=50.0,
        time_series={},
        summary_metrics={"mean_deviation": 1.25, "max_tolerance": 100.0},
    )

    raw_data = RawFactoryDataDto(
        baseline_name="Line_1_Digital_Twin",
        source_log_path=str(fake_log_file),
    )

    metrics = usecase.execute(raw_data, valid_ctx)

    assert metrics.sync_error_rate == 1.25
    assert metrics.sync_status == TwinSyncStatus.COMPLETED.value
    assert metrics.is_verified is True
    assert mock_command_repo.save.call_count == 1
    assert not os.path.exists(str(fake_log_file))


def test_tc_edge_case_tolerance_exceeded(
    usecase: ReconstructTwinUseCase,
    mock_sensor_parser: MagicMock,
    mock_command_repo: MagicMock,
    valid_ctx: UserContext,
    tmp_path,
):
    """[TC-예외] 오차율 초과 시(15.3% > 5.0%) 저장 후 ERR_TWIN_SYNC_OVER_LIMIT 발생 및 파일 정리 검증"""
    fake_log_file = tmp_path / "sensor_bad_sample.csv"
    fake_log_file.write_text("timestamp,deviation\n1,15.3\n")

    mock_sensor_parser.parse.return_value = ParsedSensorLogDto(
        file_name="sensor_bad_sample.csv",
        total_samples=1,
        sampling_rate_hz=50.0,
        time_series={},
        summary_metrics={"mean_deviation": 15.3, "max_tolerance": 100.0},
    )

    raw_data = RawFactoryDataDto(
        baseline_name="Line_2_Digital_Twin",
        source_log_path=str(fake_log_file),
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(raw_data, valid_ctx)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SYNC_OVER_LIMIT
    assert mock_command_repo.save.call_count == 1
    saved_entity = mock_command_repo.save.call_args[0][0]
    assert saved_entity.sync_status == TwinSyncStatus.TOLERANCE_EXCEEDED
    assert not os.path.exists(str(fake_log_file))


def test_tc_error_handling_sensor_parse_fail(
    usecase: ReconstructTwinUseCase,
    mock_sensor_parser: MagicMock,
    mock_command_repo: MagicMock,
    valid_ctx: UserContext,
    tmp_path,
):
    """[TC-에러] 파싱 실패 시 예외 전파 및 save 미호출, 임시 파일 정리 검증"""
    fake_log_file = tmp_path / "broken_sensor.csv"
    fake_log_file.write_text("broken,data\n")

    mock_sensor_parser.parse.side_effect = BaseSystemException.from_error_code(
        GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
        custom_message="Sensor log file corrupted.",
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(
            raw_data=RawFactoryDataDto(
                baseline_name="Fail_Baseline",
                source_log_path=str(fake_log_file),
            ),
            ctx=valid_ctx,
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL
    mock_command_repo.save.assert_not_called()
    assert not os.path.exists(str(fake_log_file))
