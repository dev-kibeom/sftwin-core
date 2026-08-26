from unittest.mock import MagicMock

import pytest
from shared.context.user_context import UserContext
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto
from simulation.contracts.ports.outbound.i_bypass_planner import IBypassPlanner
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_request_dto import (
    PlanBypassRecoveryRequestDto,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_result_dto import (
    PlanBypassRecoveryResultDto,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_usecase import (
    PlanBypassRecoveryUseCase,
)


@pytest.fixture
def mock_bypass_planner() -> MagicMock:
    return MagicMock(spec=IBypassPlanner)


@pytest.fixture
def usecase(
    mock_bypass_planner: MagicMock,
    mock_script_loader: MagicMock,
) -> PlanBypassRecoveryUseCase:
    return PlanBypassRecoveryUseCase(
        bypass_planner=mock_bypass_planner,
    )


def test_tc_plan_bypass_recovery_success(
    usecase: PlanBypassRecoveryUseCase,
    mock_bypass_planner: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 유효한 스크립트와 시나리오 기반 우회 궤적 산출 성공 검증"""
    req_dto = PlanBypassRecoveryRequestDto(
        scenario_id="SCENARIO-01",
        sequence_script="<root>valid</root>",
        trigger_time_sec=5.0,
        obstacle_distance_m=2.0,
    )

    mock_point = TrajectoryPointDto(
        time_sec=0.1,
        asset_id="ROBOT-01",
        position_x=1.0,
        position_y=2.0,
        position_z=0.0,
        velocity=0.5,
    )
    mock_bypass_planner.plan_bypass_trajectory.return_value = [mock_point]

    result = usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert isinstance(result, PlanBypassRecoveryResultDto)
    assert len(result.waypoints) == 1
    assert result.waypoints[0].position_x == 1.0
