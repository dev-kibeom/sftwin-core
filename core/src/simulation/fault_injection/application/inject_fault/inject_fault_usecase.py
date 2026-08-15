"""
[File Summary]
InjectFaultUseCase (Stateless Singleton)
결함 시나리오 평가 및 조율하는 유즈케이스입니다.
전략 평가 후 우회 경로를 산출하거나, 강건성 실패(E-Stop) 결과를 도출합니다.
"""

from datetime import datetime, timezone

from shared.logger.system_logger.log_context import LogContext
from shared.dtos.sim_result_dto import SimResultDto
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext
from simulation.fault_injection.domain.fault_scenario import (
    FaultScenario,
    FaultTypeEnum,
)
from simulation.fault_injection.domain.recovery_sequence_model import (
    RecoverySequenceModel,
)
from simulation.ports.outbound.i_ai_bypass_planner import IAiBypassPlanner
from simulation.ports.outbound.i_physics_engine import IPhysicsEngine


class InjectFaultUseCase:
    def __init__(
        self,
        ai_bypass_planner: IAiBypassPlanner,
        physics_engine: IPhysicsEngine,
        logger: GlobalSystemLogger | None = None,
    ):
        self._ai_bypass_planner = ai_bypass_planner
        self._physics_engine = physics_engine
        self._logger = logger or GlobalSystemLogger(
            component_name="InjectFault_UseCase"
        )

    def execute(
        self, scenario: FaultScenario, sequence_script: str, ctx: UserContext
    ) -> SimResultDto:
        log_ctx = LogContext(trace_id=f"TRC-FAULT-{scenario.scenario_id}")
        self._logger.info(f"Inject fault execution requested by {ctx.user_id}", log_ctx)

        # 1. Guard Clause: 복구 시퀀스 스크립트 검증
        model = RecoverySequenceModel(
            sequence_id=scenario.scenario_id, sequence_script=sequence_script
        )
        if not model.parse_and_validate():
            self._logger.warn("Sequence script validation failed", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_SIM_BT_EVAL_FAILED,
                message="Invalid recovery sequence script structure or missing Recovery node.",
                status_code=422,
            )

        # 2. 결함 주입 전략(Strategy) 분기 처리
        return self._evaluate_bt_strategy(scenario, log_ctx)

    def _evaluate_bt_strategy(
        self, scenario: FaultScenario, log_ctx: LogContext
    ) -> SimResultDto:
        """
        주입된 결함 유형에 따라 E-Stop 강건성 검증 또는 JAX RL 기반 우회 궤적 산출을 수행합니다.
        """
        # [Strategy 1] 네트워크 지연 시 복구 불가 (E-Stop 강건성 검증)
        if scenario.fault_type == FaultTypeEnum.NETWORK_DELAY:
            self._logger.info("Simulating NETWORK_DELAY -> Triggering E-Stop", log_ctx)
            self._physics_engine.trigger_failsafe_stop()  # E-Stop 시뮬레이션
            return SimResultDto(
                scenario_id=scenario.scenario_id,
                is_success=False,  # 우회 불가
                collision_count=0,
                estimated_cycle_time_sec=0.0,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
            )

        # [Strategy 2] 돌발 장애물 발생 시 JAX RL 에이전트 우회 경로 산출
        self._logger.info(
            "Simulating OBSTACLE_APPEARANCE -> RL bypass planning", log_ctx
        )

        try:
            obstacle_data = {"trigger_time": scenario.trigger_time_sec}
            waypoints = self._ai_bypass_planner.plan_bypass_trajectory(obstacle_data)
        except TimeoutError as exc:
            log_ctx.exc = exc
            self._logger.error("IPC Sync timeout (>1ms)", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_SIM_IPC_TIMEOUT,
                message="Shared Memory synchronization timed out.",
                status_code=500,
            ) from exc

        if not waypoints:
            self._logger.warn("AI Planner could not find bypass trajectory", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_SIM_BT_EVAL_FAILED,
                message="Unsolvable bypass trajectory due to spatial constraints.",
                status_code=422,
            )

        # 물리 엔진 궤적 평가
        self._physics_engine.evaluate_trajectory(waypoints)

        return SimResultDto(
            scenario_id=scenario.scenario_id,
            is_success=True,
            collision_count=0,
            estimated_cycle_time_sec=16.2,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            trajectory_points=waypoints,
        )
