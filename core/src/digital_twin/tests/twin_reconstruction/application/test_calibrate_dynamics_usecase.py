from unittest.mock import MagicMock

import pytest
from digital_twin.contracts.dtos.calibrate_dynamics_dto import (
    CalibrateDynamicsRequestDto,
)
from digital_twin.contracts.dtos.parsed_sensor_log_dto import ParsedSensorLogDto
from digital_twin.contracts.ports.outbound.i_baseline_command_repository import (
    IBaselineCommandRepository,
)
from digital_twin.contracts.ports.outbound.i_sensor_log_parser import ISensorLogParser
from digital_twin.twin_reconstruction.application.calibrate_dynamics.calibrate_dynamics_usecase import (
    CalibrateDynamicsUseCase,
)
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
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
    parser = MagicMock(spec=ISensorLogParser)
    parser.parse.return_value = ParsedSensorLogDto(
        file_name="sample_01.csv",
        total_samples=1000,
        sampling_rate_hz=100.0,
        time_series={"joint_1": [0.1, 0.2, 0.3]},
        summary_metrics={"mean_deviation": 0.03, "max_tolerance": 1.0},
    )
    return parser


@pytest.fixture
def mock_command_repo() -> MagicMock:
    return MagicMock(spec=IBaselineCommandRepository)


@pytest.fixture
def sample_user_context() -> UserContext:
    return UserContext(
        user_id="ENG-001",
        username="test_engineer",
        company_id="COMP-SFTWIN",
        role=UserRole.FIELD_ENGINEER,
    )


class TestCalibrateDynamicsUseCase:
    """파라미터 피팅 및 캘리브레이션 유스케이스 테스트"""

    def test_execute_successful_calibration_convergence(
        self,
        mock_sensor_parser: MagicMock,
        mock_command_repo: MagicMock,
        sample_user_context: UserContext,
    ) -> None:
        # Given: 초기 오차율 12.0%의 베이스라인 준비
        baseline = TwinBaseline(
            baseline_id="BASE-CALIB-001",
            baseline_name="Line-A-Twin",
            company_id="COMP-SFTWIN",
            sync_error_rate=12.0,
            sync_status=TwinSyncStatus.TOLERANCE_EXCEEDED,
        )
        mock_command_repo.find_by_id.return_value = baseline

        usecase = CalibrateDynamicsUseCase(
            sensor_parser=mock_sensor_parser,
            command_repo=mock_command_repo,
        )

        request_dto = CalibrateDynamicsRequestDto(
            baseline_id="BASE-CALIB-001",
            source_log_path="/data/sample.csv",
            target_tolerance_percent=5.0,
            max_iterations=10,
            initial_parameters={"joint_damping": 0.5, "friction_loss": 0.1},
        )

        # When
        response = usecase.execute(request_dto, ctx=sample_user_context)

        # Then
        assert response.baseline_id == "BASE-CALIB-001"
        assert response.is_converged is True
        assert response.final_error_rate_percent <= 5.0
        assert response.iterations_run > 0
        assert "joint_damping" in response.tuned_parameters
        assert mock_command_repo.save.called
        assert baseline.sync_error_rate <= 5.0

    def test_raise_error_when_sensor_log_parsing_fails(
        self,
        mock_sensor_parser: MagicMock,
        mock_command_repo: MagicMock,
        sample_user_context: UserContext,
    ) -> None:
        mock_sensor_parser.parse.side_effect = RuntimeError("File I/O corrupt")

        usecase = CalibrateDynamicsUseCase(
            sensor_parser=mock_sensor_parser,
            command_repo=mock_command_repo,
        )

        request_dto = CalibrateDynamicsRequestDto(
            baseline_id="BASE-CALIB-001",
            source_log_path="/invalid/path.csv",
        )

        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto, ctx=sample_user_context)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL

    def test_raise_error_when_baseline_not_found(
        self,
        mock_sensor_parser: MagicMock,
        mock_command_repo: MagicMock,
        sample_user_context: UserContext,
    ) -> None:
        mock_command_repo.find_by_id.return_value = None

        usecase = CalibrateDynamicsUseCase(
            sensor_parser=mock_sensor_parser,
            command_repo=mock_command_repo,
        )

        request_dto = CalibrateDynamicsRequestDto(
            baseline_id="BASE-NONEXISTENT",
            source_log_path="/data/sample.csv",
        )

        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto, ctx=sample_user_context)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND

    def test_raise_error_when_company_id_mismatch(
        self,
        mock_sensor_parser: MagicMock,
        mock_command_repo: MagicMock,
        sample_user_context: UserContext,
    ) -> None:
        # 타 테넌트 데이터 조회 시도
        baseline = TwinBaseline(
            baseline_id="BASE-OTHER-001",
            baseline_name="Other-Twin",
            company_id="COMP-OTHER",
        )
        mock_command_repo.find_by_id.return_value = baseline

        usecase = CalibrateDynamicsUseCase(
            sensor_parser=mock_sensor_parser,
            command_repo=mock_command_repo,
        )

        request_dto = CalibrateDynamicsRequestDto(
            baseline_id="BASE-OTHER-001",
            source_log_path="/data/sample.csv",
        )

        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto, ctx=sample_user_context)

        assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
