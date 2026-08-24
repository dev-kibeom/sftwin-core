from unittest.mock import MagicMock

import pytest
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole
from simulation.contracts.dtos.deploy_package_dto import DeployPackageDto
from simulation.contracts.ports.outbound.i_fleet_deployment_gateway import (
    IFleetDeploymentGateway,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_request_dto import (
    DeploySim2RealRequestDto,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_result_dto import (
    DeploySim2RealResultDto,
)
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_usecase import (
    DeploySim2RealUseCase,
)


@pytest.fixture
def mock_gateway() -> MagicMock:
    return MagicMock(spec=IFleetDeploymentGateway)


@pytest.fixture
def usecase(mock_gateway: MagicMock) -> DeploySim2RealUseCase:
    return DeploySim2RealUseCase(gateway=mock_gateway)


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_deploy_sim2real(
    usecase: DeploySim2RealUseCase,
    mock_gateway: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 패키지 생성 및 배포 게이트웨이 호출 성공 검증"""
    req_dto = DeploySim2RealRequestDto(
        package_id="PKG-100",
        format_type="ROS2_WS",
        ros2_ws_path="/opt/ros2_ws",
        config={"headerId": 1},
    )

    result = usecase.execute(request_dto=req_dto, ctx=standard_context)

    mock_gateway.deploy.assert_called_once()
    called_dto = mock_gateway.deploy.call_args[0][0]
    assert isinstance(called_dto, DeployPackageDto)
    assert called_dto.package_id == "PKG-100"
    assert called_dto.format_type == "ROS2_WS"

    assert isinstance(result, DeploySim2RealResultDto)
    assert result.package_id == "PKG-100"
    assert result.is_success is True
    assert len(result.package_hash) == 64


def test_tc_edge_case_gateway_io_error(
    usecase: DeploySim2RealUseCase,
    mock_gateway: MagicMock,
    standard_context: UserContext,
):
    """[TC-예외] 배포 전송 실패 시 500 ERR_COMMON_INTERNAL_ERROR 발생 검증"""
    mock_gateway.deploy.side_effect = OSError("Network unreachable")

    req_dto = DeploySim2RealRequestDto(
        package_id="PKG-100",
        format_type="ROS2_WS",
        ros2_ws_path="/opt/ros2_ws",
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
    assert exc_info.value.status_code == 500
