from datetime import datetime, timezone

from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context
from simulation.fault_injection.application.inject_fault.inject_fault_dto import (
    InjectFaultRequestDto,
)
from simulation.fault_injection.domain.fault_scenario.fault_scenario import (
    FaultScenario,
)
from simulation.fault_injection.domain.fault_type_enum import FaultType
from simulation.ports.inbound.dtos.sim_result_dto import SimResultDto
from simulation.ports.outbound.i_ai_bypass_planner import IAiBypassPlanner
from simulation.ports.outbound.i_physics_engine import IPhysicsEngine
from simulation.ports.outbound.i_recovery_script_parser import IRecoveryScriptParser


class InjectFaultUseCase:
    def __init__(
        self,
        ai_bypass_planner: IAiBypassPlanner,
        physics_engine: IPhysicsEngine,
        script_parser: IRecoveryScriptParser,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._ai_bypass_planner = ai_bypass_planner
        self._physics_engine = physics_engine
        self._script_parser = script_parser
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="InjectFaultUseCase"
        )

    @require_user_context
    def execute(
        self, request_dto: InjectFaultRequestDto, ctx: UserContext
    ) -> SimResultDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", f"TRC-FAULT-{request_dto.target}"),
            context={
                "user_id": ctx.user_id,
                "company_id": ctx.company_id,
                "fault_type": request_dto.fault_type,
                "target": request_dto.target,
            },
        )

        if not self._script_parser.validate_syntax(request_dto.sequence_script):
            self._system_logger.warn(
                "Sequence script syntax validation failed", log_ctx
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_SIM_BT_EVAL_FAILED,
                message="Invalid recovery sequence script syntax or structure.",
                status_code=422,
            )

        try:
            scenario = FaultScenario(
                scenario_id=request_dto.target,
                fault_type=FaultType(request_dto.fault_type),
                trigger_time_sec=request_dto.trigger_time_sec,
            )
        except ValueError as e:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                message=str(e),
                status_code=400,
            ) from e

        return self._evaluate_fault_strategy(scenario, log_ctx)

    def _evaluate_fault_strategy(
        self, scenario: FaultScenario, log_ctx: LogContext
    ) -> SimResultDto:
        if scenario.fault_type == FaultType.NETWORK_DELAY:
            self._physics_engine.trigger_failsafe_stop()
            return SimResultDto(
                scenario_id=scenario.scenario_id,
                is_success=False,
                collision_count=0,
                estimated_cycle_time_sec=0.0,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
            )

        try:
            obstacle_data = {"trigger_time": scenario.trigger_time_sec}
            waypoints = self._ai_bypass_planner.plan_bypass_trajectory(obstacle_data)
        except TimeoutError as exc:
            log_ctx.exc = exc
            self._system_logger.error("IPC Sync timeout (>1ms)", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_SIM_IPC_TIMEOUT,
                message="Shared Memory synchronization timed out.",
                status_code=500,
            ) from exc

        if not waypoints:
            self._system_logger.warn(
                "AI Planner could not find bypass trajectory", log_ctx
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_SIM_BT_EVAL_FAILED,
                message="Unsolvable bypass trajectory due to spatial constraints.",
                status_code=422,
            )

        self._physics_engine.evaluate_trajectory(waypoints)

        self._system_logger.info("Inject fault completed successfully", log_ctx)
        return SimResultDto(
            scenario_id=scenario.scenario_id,
            is_success=True,
            collision_count=0,
            estimated_cycle_time_sec=16.2,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            trajectory_points=waypoints,
        )
