from unittest.mock import MagicMock

import pytest
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from simulation.contracts.dtos.trajectory_point_dto import TrajectoryPointDto
from simulation.contracts.ports.outbound.i_bypass_planner import IBypassPlanner
from simulation.contracts.ports.outbound.i_recovery_script_loader import (
    IRecoveryScriptLoader,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_request_dto import (
    PlanBypassRecoveryRequestDto,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_result_dto import (
    PlanBypassRecoveryResultDto,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_usecase import (
    PlanBypassRecoveryUseCase,
)
from simulation.fault_recovery.domain.recovery_sequence.recovery_sequence import (
    RecoverySequence,
)


@pytest.fixture
def mock_bypass_planner() -> MagicMock:
    return MagicMock(spec=IBypassPlanner)


@pytest.fixture
def mock_script_loader() -> MagicMock:
    loader = MagicMock(spec=IRecoveryScriptLoader)
    loader.load_and_validate.return_value = RecoverySequence(
        sequence_id="SEQ-01",
        sequence_script="<root>valid_behavior_tree_xml</root>",
    )
    return loader


@pytest.fixture
def usecase(
    mock_bypass_planner: MagicMock,
    mock_script_loader: MagicMock,
) -> PlanBypassRecoveryUseCase:
    return PlanBypassRecoveryUseCase(
        bypass_planner=mock_bypass_planner,
        script_loader=mock_script_loader,
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


def test_tc_invalid_recovery_script_raises_error(
    usecase: PlanBypassRecoveryUseCase,
    mock_script_loader: MagicMock,
    standard_context: UserContext,
):
    """[TC-예외] 스크립트 검증 실패 시 ERR_SIM_RECOVER_EVAL_FAILED 발생 검증"""
    mock_script_loader.load_and_validate.return_value = None

    req_dto = PlanBypassRecoveryRequestDto(
        scenario_id="SCENARIO-01",
        sequence_script="<invalid>syntax",
        trigger_time_sec=5.0,
    )

    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(request_dto=req_dto, ctx=standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED
