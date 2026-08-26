from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context
from simulation.contracts.ports.outbound.i_bypass_planner import IBypassPlanner
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_request_dto import (
    PlanBypassRecoveryRequestDto,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_result_dto import (
    PlanBypassRecoveryResultDto,
)


class PlanBypassRecoveryUseCase:
    """IBypassPlanner를 통한 우회 경로 산출 전담 유스케이스"""

    def __init__(
        self,
        bypass_planner: IBypassPlanner,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._bypass_planner = bypass_planner
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="PlanBypassRecoveryUseCase"
        )

    @require_user_context
    def execute(
        self, request_dto: PlanBypassRecoveryRequestDto, ctx: UserContext
    ) -> PlanBypassRecoveryResultDto:

        bypass_waypoints = self._bypass_planner.plan_bypass_trajectory(
            obstacle_data={
                "trigger_time": request_dto.trigger_time_sec,
                "obstacle_distance_m": request_dto.obstacle_distance_m,
            }
        )

        if not bypass_waypoints:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED,
                custom_message="Planner failed to generate feasible bypass waypoints.",
            )

        return PlanBypassRecoveryResultDto(
            scenario_id=request_dto.scenario_id,
            waypoints=tuple(bypass_waypoints),
        )
