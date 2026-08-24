from datetime import datetime, timezone

from digital_twin.contracts.dtos.asset_dto import AssetDto
from shared.context.user_context import UserContext
from shared.security.context_guard import require_user_context
from simulation.contracts.dtos.sim_result_dto import SimResultDto
from simulation.fault_recovery.application.inject_fault.inject_fault_request_dto import (
    InjectFaultRequestDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_usecase import (
    InjectFaultUseCase,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_request_dto import (
    PlanBypassRecoveryRequestDto,
)
from simulation.fault_recovery.application.plan_bypass_recovery.plan_bypass_recovery_usecase import (
    PlanBypassRecoveryUseCase,
)
from simulation.fault_recovery.domain.failsafe_recovery_policy.safety_action_enum import (
    SafetyAction,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_request_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_usecase import (
    RunFmsSimulationUseCase,
)


class SimulateFaultRecoveryScenarioUseCase:
    """결함 주입, Failsafe 판정, 우회 계획 및 FMS 검증을 조율하는 통합 시나리오 유스케이스"""

    def __init__(
        self,
        inject_fault_uc: InjectFaultUseCase,
        plan_recovery_uc: PlanBypassRecoveryUseCase,
        run_fms_uc: RunFmsSimulationUseCase,
    ) -> None:
        self._inject_fault_uc = inject_fault_uc
        self._plan_recovery_uc = plan_recovery_uc
        self._run_fms_uc = run_fms_uc

    @require_user_context
    def execute(
        self,
        fault_request_dto: InjectFaultRequestDto,
        sequence_script: str,
        assets: tuple[AssetDto, ...],
        ctx: UserContext,
    ) -> SimResultDto:
        # 1. 결함 주입 및 Failsafe 정책 평가
        eval_result = self._inject_fault_uc.execute(
            request_dto=fault_request_dto, ctx=ctx
        )

        # 2. 비상 정지 상태일 경우 정책에 따라 즉시 실패 처리 반환
        if eval_result.action == SafetyAction.MAINTAIN_ESTOP:
            return SimResultDto(
                scenario_id=eval_result.scenario_id,
                is_success=False,
                collision_count=0,
                estimated_cycle_time_sec=0.0,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
                trajectory_points=(),
            )

        # 3. 우회 복구 궤적 산출
        recovery_result = self._plan_recovery_uc.execute(
            request_dto=PlanBypassRecoveryRequestDto(
                scenario_id=eval_result.scenario_id,
                sequence_script=sequence_script,
                trigger_time_sec=fault_request_dto.trigger_time_sec,
                obstacle_distance_m=fault_request_dto.obstacle_distance_m,
            ),
            ctx=ctx,
        )

        # 4. 타입 안정성이 보장된 DTO로 FMS 시뮬레이션 가동 및 물리 검증 수행
        fms_request_dto = RunFmsSimulationRequestDto(
            scenario_id=f"RECOVERY-{eval_result.scenario_id}",
            baseline_id=f"BASE-{eval_result.scenario_id}",
            assets=assets,
            task_waypoints=recovery_result.waypoints,
        )

        return self._run_fms_uc.execute(request_dto=fms_request_dto, ctx=ctx)
