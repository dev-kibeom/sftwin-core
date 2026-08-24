from unittest.mock import MagicMock

import pytest
from shared.context.user_context import UserContext
from simulation.contracts.ports.outbound.i_physics_engine import IPhysicsEngine
from simulation.fault_recovery.application.inject_fault.inject_fault_request_dto import (
    InjectFaultRequestDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_result_dto import (
    InjectFaultResultDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.fault_recovery.domain.failsafe_recovery_policy.safety_action_enum import (
    SafetyAction,
)


@pytest.fixture
def mock_physics_engine() -> MagicMock:
    return MagicMock(spec=IPhysicsEngine)


@pytest.fixture
def usecase(mock_physics_engine: MagicMock) -> InjectFaultUseCase:
    return InjectFaultUseCase(physics_engine=mock_physics_engine)


def test_tc_network_delay_triggers_estop(
    usecase: InjectFaultUseCase,
    mock_physics_engine: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 네트워크 지연 시 Failsafe 정책에 따라 E-Stop 트리거 검증"""
    req_dto = InjectFaultRequestDto(
        fault_type="NETWORK_DELAY",
        target="ROBOT-01",
    )

    result = usecase.execute(request_dto=req_dto, ctx=standard_context)

    mock_physics_engine.trigger_failsafe_stop.assert_called_once()
    assert isinstance(result, InjectFaultResultDto)
    assert result.action == SafetyAction.MAINTAIN_ESTOP
    assert result.requires_bypass_planning is False


def test_tc_obstacle_appearance_allows_bypass_planning(
    usecase: InjectFaultUseCase,
    mock_physics_engine: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 안전거리 내 장애물 출현 시 우회 플래닝 승인 검증"""
    req_dto = InjectFaultRequestDto(
        fault_type="OBSTACLE_APPEARANCE",
        target="ROBOT-01",
        obstacle_distance_m=2.0,
    )

    result = usecase.execute(request_dto=req_dto, ctx=standard_context)

    mock_physics_engine.trigger_failsafe_stop.assert_not_called()
    assert isinstance(result, InjectFaultResultDto)
    assert result.action == SafetyAction.EXECUTE_BYPASS_RECOVERY
    assert result.requires_bypass_planning is True
