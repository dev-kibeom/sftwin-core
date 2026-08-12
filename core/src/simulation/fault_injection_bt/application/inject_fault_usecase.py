"""
[File Summary]
InjectFaultUseCase (Stateless Singleton)
결함 시나리오 평가 및 RL 어댑터 호출을 조율하는 유즈케이스입니다.
Behavior Tree 전략 평가 후 우회 경로를 산출하거나, 강건성 실패(E-Stop) 결과를 도출합니다.
"""

from datetime import datetime, timezone

from src.shared.dtos.log_dtos import LogContext
from src.shared.dtos.sim_result_dto import SimResultDto
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.logger.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext
from src.simulation.fault_injection_bt.domain.behavior_tree_model import (
    BehaviorTreeModel,
)
from src.simulation.fault_injection_bt.domain.fault_scenario import (
    FaultScenario,
    FaultTypeEnum,
)


class InjectFaultUseCase:
    def __init__(self, rl_planner_adapter, physics_adapter, logger: GlobalSystemLogger):
        self._rl_planner_adapter = rl_planner_adapter
        self._physics_adapter = physics_adapter
        self._logger = logger

    def execute(
        self, scenario: FaultScenario, bt_xml: str, ctx: UserContext
    ) -> SimResultDto:
        log_ctx = LogContext(trace_id=f"TRC-FAULT-{scenario.scenario_id}")
        self._logger.info(f"Inject fault execution requested by {ctx.user_id}", log_ctx)

        # 1. Guard Clause: Behavior Tree XML 검증
        bt_model = BehaviorTreeModel(tree_id=scenario.scenario_id, xml_structure=bt_xml)
        if not bt_model.parse_and_validate():
            self._logger.warn("BT XML Validation failed", log_ctx)
            raise BaseSystemException(
                error_code="ERR_SIM_BT_EVAL_FAILED",
                message="Invalid Behavior Tree XML structure or missing Recovery node.",
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
            self._physics_adapter.trigger_failsafe_stop()  # E-Stop 시뮬레이션
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
            waypoints = self._rl_planner_adapter.plan_bypass_trajectory(obstacle_data)
        except TimeoutError as exc:
            log_ctx.exc = exc
            self._logger.error("JAX RL IPC Sync timeout (>1ms)", log_ctx)
            raise BaseSystemException(
                error_code="ERR_SIM_IPC_TIMEOUT",
                message="POSIX Shared Memory synchronization with JAX RL Agent timed out.",
                status_code=500,
            )

        # RL 에이전트가 우회 경로를 찾지 못한 경우
        if not waypoints or len(waypoints) == 0:
            self._logger.warn("RL Planner could not find bypass trajectory", log_ctx)
            raise BaseSystemException(
                error_code="ERR_SIM_BT_EVAL_FAILED",
                message="Unsolvable bypass trajectory due to spatial constraints.",
                status_code=422,
            )

        # 정상 우회 시뮬레이션 연산 수행
        self._physics_adapter.evaluate_trajectory(waypoints)

        return SimResultDto(
            scenario_id=scenario.scenario_id,
            is_success=True,
            collision_count=0,
            estimated_cycle_time_sec=16.2,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            trajectory_points=waypoints,
        )
