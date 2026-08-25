from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.audit.audit_event_type_enum import AuditEventType
from shared.security.audit.audit_events import AuditEvent
from shared.security.audit.audit_severity_enum import AuditSeverity
from shared.security.audit.global_audit_logger import GlobalAuditLogger
from shared.security.context_guard import require_user_context
from simulation.contracts.ports.outbound.i_physics_engine import IPhysicsEngine
from simulation.fault_recovery.application.inject_fault.inject_fault_request_dto import (
    InjectFaultRequestDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_result_dto import (
    InjectFaultResultDto,
)
from simulation.fault_recovery.domain.failsafe_recovery_policy.failsafe_recovery_policy import (
    FailsafeRecoveryPolicy,
)
from simulation.fault_recovery.domain.failsafe_recovery_policy.safety_action_enum import (
    SafetyAction,
)
from simulation.fault_recovery.domain.fault_scenario.fault_scenario import (
    FaultScenario,
)
from simulation.fault_recovery.domain.fault_type_enum import FaultType


class InjectFaultUseCase:
    """결함 주입 및 Pure Domain Policy 기반 안전 조치 판정 유스케이스"""

    def __init__(
        self,
        physics_engine: IPhysicsEngine,
        policy: FailsafeRecoveryPolicy | None = None,
        system_logger: GlobalSystemLogger | None = None,
        audit_logger: GlobalAuditLogger | None = None,
    ) -> None:
        self._physics_engine = physics_engine
        self._policy = policy or FailsafeRecoveryPolicy()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="InjectFaultUseCase"
        )
        self._audit_logger = audit_logger or GlobalAuditLogger()

    @require_user_context
    def execute(
        self, request_dto: InjectFaultRequestDto, ctx: UserContext
    ) -> InjectFaultResultDto:
        try:
            scenario = FaultScenario(
                scenario_id=request_dto.target,
                fault_type=FaultType(request_dto.fault_type),
                trigger_time_sec=request_dto.trigger_time_sec,
                obstacle_distance_m=request_dto.obstacle_distance_m,
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        policy_result = self._policy.evaluate_fault_scenario(
            fault_type=scenario.fault_type,
            obstacle_distance_m=scenario.obstacle_distance_m,
        )

        if policy_result.action == SafetyAction.MAINTAIN_ESTOP:
            self._physics_engine.trigger_failsafe_stop()
            # Failsafe 발동 시 감사 로그 등록
            self._audit_logger.log(
                AuditEvent(
                    event_type=AuditEventType.FAILSAFE,
                    action="ENFORCE_ESTOP",
                    target=f"Scenario:{scenario.scenario_id}",
                    severity=AuditSeverity.CRITICAL,
                    user_ctx=ctx,
                    details={
                        "fault_type": scenario.fault_type.value,
                        "reason": policy_result.reason,
                    },
                )
            )
            self._system_logger.info(
                f"Enforced E-STOP by failsafe policy: {policy_result.reason}",
                extra={
                    "scenario_id": scenario.scenario_id,
                    "company_id": ctx.company_id,
                },
            )

        return InjectFaultResultDto(
            scenario_id=scenario.scenario_id,
            action=policy_result.action,
            reason=policy_result.reason,
            requires_bypass_planning=policy_result.requires_bypass_planning,
        )
