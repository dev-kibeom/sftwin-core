from unittest.mock import MagicMock

import pytest
from shared.context.user_context import UserContext
from simulation.contracts.dtos.sim_result_dto import SimResultDto
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto
from simulation.fault_recovery.application.fault_recovery_scenario.fault_recovery_scenario_usecase import (
    SimulateFaultRecoveryScenarioUseCase,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_request_dto import (
    InjectFaultRequestDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_result_dto import (
    InjectFaultResultDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_result_dto import (
    PlanBypassRecoveryResultDto,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_usecase import (
    PlanBypassRecoveryUseCase,
)
from simulation.fault_recovery.domain.failsafe_recovery_policy.safety_action_enum import (
    SafetyAction,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)


@pytest.fixture
def mock_inject_fault_uc() -> MagicMock:
    return MagicMock(spec=InjectFaultUseCase)


@pytest.fixture
def mock_plan_recovery_uc() -> MagicMock:
    return MagicMock(spec=PlanBypassRecoveryUseCase)


@pytest.fixture
def mock_run_fms_uc() -> MagicMock:
    return MagicMock(spec=RunFmsSimulationUseCase)


@pytest.fixture
def scenario_usecase(
    mock_inject_fault_uc: MagicMock,
    mock_plan_recovery_uc: MagicMock,
    mock_run_fms_uc: MagicMock,
) -> SimulateFaultRecoveryScenarioUseCase:
    return SimulateFaultRecoveryScenarioUseCase(
        inject_fault_uc=mock_inject_fault_uc,
        plan_recovery_uc=mock_plan_recovery_uc,
        run_fms_uc=mock_run_fms_uc,
    )


def test_tc_scenario_pipeline_estop_early_return(
    scenario_usecase: SimulateFaultRecoveryScenarioUseCase,
    mock_inject_fault_uc: MagicMock,
    mock_plan_recovery_uc: MagicMock,
    mock_run_fms_uc: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 결함 주입 결과가 E-Stop일 때 즉시 실패 DTO 반환 및 후속 프로세스 차단 검증"""
    mock_inject_fault_uc.execute.return_value = InjectFaultResultDto(
        scenario_id="ROBOT-01",
        action=SafetyAction.MAINTAIN_ESTOP,
        reason="Network Delay",
        requires_bypass_planning=False,
    )

    result = scenario_usecase.execute(
        fault_request_dto=InjectFaultRequestDto(
            fault_type="NETWORK_DELAY", target="ROBOT-01"
        ),
        sequence_script="<root>tree</root>",
        assets=(),
        ctx=standard_context,
    )

    assert isinstance(result, SimResultDto)
    assert result.is_success is False
    mock_plan_recovery_uc.execute.assert_not_called()
    mock_run_fms_uc.execute.assert_not_called()


def test_tc_scenario_pipeline_bypass_and_fms_execution_success(
    scenario_usecase: SimulateFaultRecoveryScenarioUseCase,
    mock_inject_fault_uc: MagicMock,
    mock_plan_recovery_uc: MagicMock,
    mock_run_fms_uc: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 우회 승인 시 플래닝 거쳐 FMS 시뮬레이션까지 전체 파이프라인 수행 검증"""
    mock_inject_fault_uc.execute.return_value = InjectFaultResultDto(
        scenario_id="ROBOT-01",
        action=SafetyAction.EXECUTE_BYPASS_RECOVERY,
        reason="Obstacle detected",
        requires_bypass_planning=True,
    )

    mock_point = TrajectoryPointDto(
        time_sec=0.1,
        asset_id="ROBOT-01",
        position_x=1.0,
        position_y=2.0,
        position_z=0.0,
        velocity=0.5,
    )
    mock_plan_recovery_uc.execute.return_value = PlanBypassRecoveryResultDto(
        scenario_id="ROBOT-01",
        waypoints=(mock_point,),
    )

    mock_run_fms_uc.execute.return_value = SimResultDto(
        scenario_id="RECOVERY-ROBOT-01",
        is_success=True,
        collision_count=0,
        estimated_cycle_time_sec=14.5,
        evaluated_at="2026-08-25T00:00:00Z",
        trajectory_points=(mock_point,),
    )

    result = scenario_usecase.execute(
        fault_request_dto=InjectFaultRequestDto(
            fault_type="OBSTACLE_APPEARANCE", target="ROBOT-01"
        ),
        sequence_script="<root>tree</root>",
        assets=(),
        ctx=standard_context,
    )

    assert isinstance(result, SimResultDto)
    assert result.is_success is True
    mock_inject_fault_uc.execute.assert_called_once()
    mock_plan_recovery_uc.execute.assert_called_once()
    mock_run_fms_uc.execute.assert_called_once()
