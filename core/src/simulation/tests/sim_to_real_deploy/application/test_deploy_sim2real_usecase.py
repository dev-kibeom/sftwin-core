from unittest.mock import Mock

import pytest
from shared.context.user_context import UserContext
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException
from simulation.ports.outbound.i_fleet_deploy import IFleetDeploy
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_dto import (
    DeploySim2RealRequestDto,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)
from simulation.sim_to_real_deploy.domain.deploy_package.deploy_package_format_enum import (
    DeployPackageFormat,
)


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_adapter():
    return Mock(spec=IFleetDeploy)


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="usr-123",
        username="test",
        company_id="cmp-1",
        role=UserRole.SI_PARTNER,
    )


class TestDeploySim2RealUseCase:
    def test_happy_path_deploy_success(self, mock_adapter, mock_logger, valid_ctx):
        """TC-정상: Sim-to-Real 배포 패키지 추출 성공"""
        # Given
        package_id = "pkg-valid-001"
        mock_adapter.export_package.return_value = True
        usecase = DeploySim2RealUseCase(mock_adapter, mock_logger)
        request_dto = DeploySim2RealRequestDto(
            package_id=package_id,
            format_type="ROS2_WS",
            config={"robot_ip": "192.168.1.100"},
        )

        # When
        result = usecase.execute(request_dto=request_dto, ctx=valid_ctx)

        # Then
        assert result is True
        mock_adapter.export_package.assert_called_once()
        called_pkg = mock_adapter.export_package.call_args[0][0]
        assert called_pkg.package_id == package_id
        assert called_pkg.format == DeployPackageFormat.ROS2_WS
        assert len(called_pkg.package_hash) > 0

    def test_edge_case_unverified_scenario(self, mock_adapter, mock_logger, valid_ctx):
        """TC-예외: 미검증 시나리오 추출 시도 차단 (400 Bad Request)"""
        # Given
        usecase = DeploySim2RealUseCase(mock_adapter, mock_logger)
        request_dto = DeploySim2RealRequestDto(
            package_id="pkg-invalid-002",
            format_type="ROS2_WS",
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_ctx)

        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
        mock_adapter.export_package.assert_not_called()

    def test_error_io_exception_masking(self, mock_adapter, mock_logger, valid_ctx):
        """TC-에러: 어댑터 I/O 오류 발생 시 500 예외 마스킹 처리"""
        # Given
        mock_adapter.export_package.side_effect = OSError(
            "Permission denied to /opt/sftwin/deploy"
        )
        usecase = DeploySim2RealUseCase(mock_adapter, mock_logger)
        request_dto = DeploySim2RealRequestDto(
            package_id="pkg-valid-003",
            format_type="VDA_5050",
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            usecase.execute(request_dto=request_dto, ctx=valid_ctx)

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
