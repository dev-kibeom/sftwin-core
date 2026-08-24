from datetime import datetime, timezone

from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context
from simulation.contracts.dtos.sim_result_dto import SimResultDto
from simulation.contracts.ports.outbound.i_physics_engine import IPhysicsEngine
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_request_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.fms_execution.domain.collision_detector import (
    CollisionDetector,
    TrajectoryPoint,
)
from simulation.fms_execution.domain.fms_scenario.fms_scenario import FmsScenario


class RunFmsSimulationUseCase:
    """FMS 시뮬레이션 가동 및 충돌/데드락 검증을 오케스트레이션하는 유스케이스"""

    def __init__(
        self,
        physics_engine: IPhysicsEngine,
        collision_detector: CollisionDetector | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._physics_engine = physics_engine
        self._collision_detector = collision_detector or CollisionDetector()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="RunFmsSimulationUseCase"
        )

    @require_user_context
    def execute(
        self,
        request_dto: RunFmsSimulationRequestDto,
        ctx: UserContext,
    ) -> SimResultDto:
        # 1. 도메인 시나리오 생성 및 불변식 검증 (company_id 바인딩)
        try:
            scenario = FmsScenario.create(
                scenario_id=request_dto.scenario_id,
                baseline_id=request_dto.baseline_id,
                company_id=ctx.company_id,
                raw_assets=request_dto.assets,
                task_waypoints=request_dto.task_waypoints,
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_SIM_INVALID_SCENARIO,
                custom_message=str(e),
            ) from e

        # 2. 물리 동역학 연산 실행 (VRAM/하드웨어 예외는 PhysicsEngine 어댑터에서 BaseSystemException으로 전파)
        trajectory_dtos = self._physics_engine.simulate_scenario(scenario)

        trajectory_points = [
            TrajectoryPoint(
                time_sec=p.time_sec,
                asset_id=p.asset_id,
                position_x=p.position_x,
                position_y=p.position_y,
                position_z=p.position_z,
                velocity=p.velocity,
                is_collided=p.is_collided,
            )
            for p in trajectory_dtos
        ]

        # 3. 도메인 충돌 검출 서비스 실행
        detection_res = CollisionDetector.detect(trajectory_points)
        if detection_res.is_collided:
            self._system_logger.warn(
                f"Collision detected in scenario '{scenario.scenario_id}'. Count: {detection_res.collision_count}",
                extra={
                    "scenario_id": scenario.scenario_id,
                    "collision_count": detection_res.collision_count,
                    "company_id": ctx.company_id,
                },
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_SIM_COLLISION_DETECTED,
                details={"collision_count": detection_res.collision_count},
            )

        # 4. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"FMS Simulation completed successfully for scenario: {scenario.scenario_id}",
            extra={
                "scenario_id": scenario.scenario_id,
                "baseline_id": scenario.baseline_id,
                "company_id": ctx.company_id,
                "trajectory_count": len(trajectory_dtos),
            },
        )

        # 5. 반환 DTO 조립
        return SimResultDto(
            scenario_id=scenario.scenario_id,
            is_success=True,
            collision_count=detection_res.collision_count,
            estimated_cycle_time_sec=14.5,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            trajectory_points=tuple(trajectory_dtos),
        )
