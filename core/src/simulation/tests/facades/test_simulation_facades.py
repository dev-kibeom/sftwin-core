from unittest.mock import Mock

import pytest
from shared.context.user_context import UserContext
from shared.enums.user_role_enum import UserRoleEnum
from simulation.facades.simulation_command_facade import SimulationCommandFacade
from simulation.facades.simulation_query_facade import SimulationQueryFacade
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.ports.inbound.dtos.sim_result_dto import SimResultDto
from simulation.sim_to_real_deploy.application.deploy_sim2real.deploy_sim2real_dto import (
    DeploySim2RealRequestDto,
)


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="usr-facade-01",
        username="facade_tester",
        company_id="cmp-facade",
        role=UserRoleEnum.SYSTEM_ADMIN,
    )


def test_command_facade_delegation(valid_ctx):
    """Command Facade가 각 유스케이스로 올바르게 위임하는지 검증"""
    mock_run_fms = Mock()
    mock_inject_fault = Mock()
    mock_deploy = Mock()
    mock_optimize = Mock()

    expected_sim_result = SimResultDto("scn-1", True, 0, 10.0, "2026-08-18T00:00:00Z")
    mock_run_fms.execute.return_value = expected_sim_result
    mock_deploy.execute.return_value = True

    facade = SimulationCommandFacade(
        run_fms_uc=mock_run_fms,
        inject_fault_uc=mock_inject_fault,
        deploy_uc=mock_deploy,
        optimize_layout_uc=mock_optimize,
    )

    # 1. run_fms_simulation 위임
    req_fms = RunFmsSimulationRequestDto("scn-1", "base-1", [])
    result = facade.run_fms_simulation(req_fms, valid_ctx)
    assert result == expected_sim_result
    mock_run_fms.execute.assert_called_once_with(request_dto=req_fms, ctx=valid_ctx)

    # 2. deploy_sim2real_package 위임
    req_deploy = DeploySim2RealRequestDto("pkg-1", "ROS2_WS")
    deploy_result = facade.deploy_sim2real_package(req_deploy, valid_ctx)
    assert deploy_result is True
    mock_deploy.execute.assert_called_once_with(request_dto=req_deploy, ctx=valid_ctx)


def test_query_facade_get_status(valid_ctx):
    """Query Facade의 읽기 쿼리 응답 검증"""
    facade = SimulationQueryFacade()
    status = facade.get_simulation_status("scn-query-999", valid_ctx)

    assert status["scenario_id"] == "scn-query-999"
    assert status["company_id"] == "cmp-facade"
    assert status["status"] == "COMPLETED"
    assert status["progress_percentage"] == 100.0
