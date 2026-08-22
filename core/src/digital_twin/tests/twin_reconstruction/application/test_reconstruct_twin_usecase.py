import os
from unittest.mock import MagicMock

import pytest
from digital_twin.ports.outbound.i_baseline_command_repository import (
    IBaselineCommandRepository,
)
from digital_twin.ports.outbound.i_sensor_log_parser import ISensorLogParser
from digital_twin.twin_reconstruction.application.reconstruct_twin.raw_factory_data_dto import (
    RawFactoryDataDto,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    ReconstructTwinUseCase,
)
from shared.enums.twin_sync_status_enum import (
    TwinSyncStatus,
)
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.enums.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException


@pytest.fixture
def mock_sensor_parser():
    return MagicMock(spec=ISensorLogParser)


@pytest.fixture
def mock_command_repo():
    repo = MagicMock(spec=IBaselineCommandRepository)
    repo.save.side_effect = lambda entity: entity
    return repo


@pytest.fixture
def usecase(mock_sensor_parser, mock_command_repo):
    return ReconstructTwinUseCase(
        sensor_parser=mock_sensor_parser,
        command_repo=mock_command_repo,
        default_tolerance=5.0,
    )


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=[],
    )


def test_tc_happy_path_reconstruct_twin(
    usecase, mock_sensor_parser, mock_command_repo, valid_ctx, tmp_path
):
    """
    [TC-정상] 가상 공장 복각 및 정합성 검증 성공 시나리오
    """
    # Given
    fake_log_file = tmp_path / "sensor_sample.csv"
    fake_log_file.write_text("timestamp,deviation\n1,0.5\n2,0.8\n")

    # 파서가 원천 파일로부터 정제된 계측 데이터를 반환하도록 설정
    mock_sensor_parser.parse.return_value = {
        "mean_deviation": 1.25,
        "max_tolerance": 100.0,
    }

    raw_data = RawFactoryDataDto(
        baseline_name="Line_1_Digital_Twin",
        source_log_path=str(fake_log_file),
    )

    # When
    metrics = usecase.execute(raw_data, valid_ctx)

    # Then
    assert metrics.sync_error_rate == 1.25
    assert metrics.sync_status == TwinSyncStatus.COMPLETED.value
    assert metrics.is_verified is True
    assert mock_command_repo.save.call_count == 1
    # Clean-up 검증: 임시 원본 파일이 정상 삭제되었는지 확인
    assert not os.path.exists(str(fake_log_file))


def test_tc_edge_case_tolerance_exceeded(
    usecase, mock_sensor_parser, mock_command_repo, valid_ctx, tmp_path
):
    """
    [TC-예외] 가상-현실 정합성 오차율 허용치 초과 시나리오 (15.3% > 5.0%)
    """
    # Given
    fake_log_file = tmp_path / "sensor_bad_sample.csv"
    fake_log_file.write_text("timestamp,deviation\n1,15.3\n")

    mock_sensor_parser.parse.return_value = {
        "mean_deviation": 15.3,
        "max_tolerance": 100.0,
    }

    raw_data = RawFactoryDataDto(
        baseline_name="Line_2_Digital_Twin",
        source_log_path=str(fake_log_file),
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(raw_data, valid_ctx)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SYNC_OVER_LIMIT
    assert exc_info.value.status_code == 422

    # 저장소에 TOLERANCE_EXCEEDED 상태로 기록되었는지 검증
    saved_entity = mock_command_repo.save.call_args[0][0]
    assert saved_entity.sync_status == TwinSyncStatus.TOLERANCE_EXCEEDED


def test_tc_error_handling_sensor_parse_fail(
    usecase, mock_sensor_parser, mock_command_repo, valid_ctx
):
    """
    [TC-에러] 센서 데이터셋 파싱 실패 및 I/O 예외 시나리오
    """
    # Given
    mock_sensor_parser.parse.side_effect = BaseSystemException.from_error_code(
        GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL,
        custom_message="Sensor log file not found.",
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(
            raw_data=RawFactoryDataDto(
                baseline_name="Fail_Baseline",
                source_log_path="/invalid/path/sensor.log",
            ),
            ctx=valid_ctx,
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL
    assert exc_info.value.status_code == 500
    mock_command_repo.save.assert_not_called()
