"""
[File Summary]
DeploySim2RealUseCase Unit Tests
FDS 4절에 명시된 TC-정상, TC-예외(미검증), TC-에러(I/O 오류) 케이스를 격리된 환경에서 검증합니다.
"""

from unittest.mock import Mock

import pytest
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.security.user_context import UserContext
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)
from simulation.sim_to_real_deploy.domain.deploy_format_enums import (
    DeployPackageFormatEnum,
)


@pytest.fixture
def mock_logger():
    return Mock()


@pytest.fixture
def mock_adapter():
    return Mock()


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="usr-123",
        username="test",
        company_id="cmp-1",
        role=UserRoleEnum.SI_PARTNER,
    )


class TestDeploySim2RealUseCase:
    def test_happy_path_deploy_success(self, mock_adapter, mock_logger, valid_ctx):
        """TC-정상: Sim-to-Real 배포 패키지 추출 성공"""
        # Given
        package_id = "pkg-valid-001"
        mock_adapter.export_package.return_value = True
        uc = DeploySim2RealUseCase(mock_adapter, mock_logger)

        # When
        result = uc.execute(
            package_id, "ROS2_WS", {"robot_ip": "192.168.1.100"}, valid_ctx
        )

        # Then
        assert result is True
        mock_adapter.export_package.assert_called_once()
        # 어댑터 호출 시 전달된 인자(DeployPackage) 검증
        called_pkg = mock_adapter.export_package.call_args[0][0]
        assert called_pkg.package_id == package_id
        assert called_pkg.format == DeployPackageFormatEnum.ROS2_WS
        assert len(called_pkg.package_hash) > 0  # 해시가 정상적으로 생성되었는지 확인

    def test_edge_case_unverified_scenario(self, mock_adapter, mock_logger, valid_ctx):
        """TC-예외: 미검증 시나리오 추출 시도 차단 (400 Bad Request)"""
        # Given
        package_id = (
            "pkg-invalid-002"  # 'invalid'가 포함되어 Guard Clause에서 필터링 됨
        )
        uc = DeploySim2RealUseCase(mock_adapter, mock_logger)

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            uc.execute(package_id, "ROS2_WS", {}, valid_ctx)

        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "ERR_COMMON_INVALID_INPUT"
        mock_adapter.export_package.assert_not_called()  # 어댑터 호출 안 됨

    def test_error_io_exception_masking(self, mock_adapter, mock_logger, valid_ctx):
        """TC-에러: 어댑터 I/O 오류 발생 시 500 예외 마스킹 처리"""
        # Given
        package_id = "pkg-valid-003"
        mock_adapter.export_package.side_effect = OSError(
            "Permission denied to /opt/sftwin/deploy"
        )
        uc = DeploySim2RealUseCase(mock_adapter, mock_logger)

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            uc.execute(package_id, "VDA_5050", {}, valid_ctx)

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == "ERR_COMMON_INTERNAL_ERROR"
