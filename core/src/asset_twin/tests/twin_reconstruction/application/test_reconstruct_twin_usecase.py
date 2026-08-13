"""
===============================================================================
[File Name] test_reconstruct_twin_usecase.py
[Location ] /tests/asset_twin/twin_reconstruction/application/test_reconstruct_twin_usecase.py
[Description] ReconstructTwinUseCase FDS 시나리오 기반 단위 테스트 (Happy Path, Tolerance Exceeded, Parse Fail)
===============================================================================
"""

import os
from unittest.mock import MagicMock

import pytest

# 1. 정화된 Core UseCase 및 Port Import
from asset_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    RawDataDto,
    ReconstructTwinUseCase,
)
from asset_twin.twin_reconstruction.domain.twin_baseline import (
    TwinBaseline,
    TwinSyncStatusEnum,
)
from asset_twin.twin_reconstruction.ports.outbound.i_sensor_log_parser import (
    ISensorLogParser,
)
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.security.user_context import UserContext


def test_tc_happy_path_reconstruct_twin(tmp_path):
    """
    [TC-정상] 가상 공장 복각 및 정합성 검증 성공 시나리오
    """
    # Given
    fake_log_file = tmp_path / "sensor_sample.csv"
    fake_log_file.write_text("timestamp,deviation\n1,0.5\n2,0.8\n")

    mock_sensor = MagicMock(spec=ISensorLogParser)
    mock_sensor.parse_sensor_log.return_value = TwinBaseline(
        baseline_name="",
        source_log_path=str(fake_log_file),
        company_id="",
        raw_sensor_summary={
            "mean_deviation": 1.25,
            "max_tolerance": 100.0,
        },  # 1.25% error
    )

    mock_command_repo = MagicMock()
    mock_command_repo.save_baseline.side_effect = lambda entity: entity

    usecase = ReconstructTwinUseCase(
        sensor_log_parser=mock_sensor,
        command_repository=mock_command_repo,
        default_tolerance=5.0,  # 5% threshold
    )

    raw_data = RawDataDto(
        baseline_name="Line_1_Digital_Twin", source_log_path=str(fake_log_file)
    )

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRoleEnum.FIELD_ENGINEER,
        accessible_factory_ids=[],
    )

    # When
    metrics = usecase.execute(raw_data, ctx)

    # Then
    assert metrics.sync_error_rate == 1.25
    assert metrics.sync_status == TwinSyncStatusEnum.COMPLETED.value
    assert metrics.is_verified is True
    assert mock_command_repo.save_baseline.call_count == 1
    # Clean-up 검증: 임시 원본 파일이 삭제되었는지 확인
    assert not os.path.exists(str(fake_log_file))


def test_tc_edge_case_tolerance_exceeded(tmp_path):
    """
    [TC-예외] 가상-현실 정합성 오차율 허용치 초과 시나리오
    """
    # Given
    fake_log_file = tmp_path / "sensor_bad_sample.csv"
    fake_log_file.write_text("timestamp,deviation\n1,15.3\n")

    mock_sensor = MagicMock(spec=ISensorLogParser)
    mock_sensor.parse_sensor_log.return_value = TwinBaseline(
        baseline_name="",
        source_log_path=str(fake_log_file),
        company_id="",
        raw_sensor_summary={
            "mean_deviation": 15.3,
            "max_tolerance": 100.0,
        },  # 15.3% error
    )

    mock_command_repo = MagicMock()
    mock_command_repo.save_baseline.side_effect = lambda entity: entity

    usecase = ReconstructTwinUseCase(
        sensor_log_parser=mock_sensor,
        command_repository=mock_command_repo,
        default_tolerance=5.0,  # 5% threshold
    )

    raw_data = RawDataDto(
        baseline_name="Line_2_Digital_Twin", source_log_path=str(fake_log_file)
    )

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRoleEnum.FIELD_ENGINEER,
        accessible_factory_ids=[],
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(raw_data, ctx)

    assert exc_info.value.error_code == GlobalErrorCodes.ERR_TWIN_SYNC_OVER_LIMIT
    assert exc_info.value.status_code == 422
    # 저장소에 TOLERANCE_EXCEEDED 상태로 기록되었는지 단언
    saved_entity = mock_command_repo.save_baseline.call_args[0][0]
    assert saved_entity.sync_status == TwinSyncStatusEnum.TOLERANCE_EXCEEDED


def test_tc_error_handling_kamp_parse_fail():
    """
    [TC-에러] 센서 데이터셋 파싱 실패 및 I/O 예외 시나리오
    """
    # Given
    mock_sensor = MagicMock(spec=ISensorLogParser)
    mock_sensor.parse_sensor_log.side_effect = BaseSystemException(
        error_code=GlobalErrorCodes.ERR_TWIN_KAMP_PARSE_FAIL,
        message="Sensor log file not found.",
        status_code=500,
    )

    mock_command_repo = MagicMock()
    usecase = ReconstructTwinUseCase(
        sensor_log_parser=mock_sensor,
        command_repository=mock_command_repo,
    )

    raw_data = RawDataDto(
        baseline_name="Missing_Twin", source_log_path="/non_existent/sensor_log.csv"
    )

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRoleEnum.FIELD_ENGINEER,
        accessible_factory_ids=[],
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(raw_data, ctx)

    assert exc_info.value.error_code == GlobalErrorCodes.ERR_TWIN_KAMP_PARSE_FAIL
    assert exc_info.value.status_code == 500
    mock_command_repo.save_baseline.assert_not_called()
