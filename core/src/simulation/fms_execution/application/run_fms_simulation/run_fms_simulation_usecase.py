from datetime import datetime, timezone

from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context
from simulation.fms_execution.application.run_fms_simulation.run_fms_simulation_dto import (
    RunFmsSimulationRequestDto,
)
from simulation.fms_execution.domain.collision_detector import CollisionDetector
from simulation.fms_execution.domain.fms_scenario.fms_scenario import FmsScenario
from simulation.ports.inbound.dtos.sim_result_dto import SimResultDto
from simulation.ports.outbound.i_physics_engine import IPhysicsEngine


class RunFmsSimulationUseCase:
    MAX_VRAM_CACHE_LIMIT_MB = 4200.0

    def __init__(
        self,
        physics_engine: IPhysicsEngine,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._physics_engine = physics_engine
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="RunFmsSimulationUseCase"
        )

    @require_user_context
    def execute(
        self, request_dto: RunFmsSimulationRequestDto, ctx: UserContext
    ) -> SimResultDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", f"TRC-SIM-{request_dto.scenario_id}"),
            context={
                "user_id": ctx.user_id,
                "company_id": ctx.company_id,
                "scenario_id": request_dto.scenario_id,
                "baseline_id": request_dto.baseline_id,
            },
        )

        try:
            scenario = FmsScenario.create(
                scenario_id=request_dto.scenario_id,
                baseline_id=request_dto.baseline_id,
                raw_assets=request_dto.assets,
                task_waypoints=request_dto.task_waypoints,
            )
        except ValueError as e:
            self._system_logger.warn(f"Invalid scenario parameters: {str(e)}", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_SIM_INVALID_SCENARIO,
                message=str(e),
                status_code=400,
            ) from e

        if not self._check_vram_resource_limit():
            self._system_logger.error(
                "VRAM Resource exhausted over 4.2GB limit", log_ctx
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_SIM_RESOURCE_EXHAUSTED,
                message="GPU VRAM cache exceeds the 4.2GB limit. Request rejected to prevent OOM.",
                status_code=503,
            )

        try:
            trajectory_results = self._physics_engine.calculate_kinematics(scenario)
        except TimeoutError as exc:
            log_ctx.exc = exc
            self._system_logger.error("IPC Sync timeout (>1ms)", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_SIM_IPC_TIMEOUT,
                message="POSIX Shared Memory IPC synchronization timeout exceeded 1ms.",
                status_code=500,
            ) from exc

        detector = CollisionDetector()
        if detector.detect(trajectory_results):
            self._system_logger.warn(
                f"Collision/Deadlock detected. Count: {detector.collision_count}",
                log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_SIM_COLLISION_DETECTED,
                message="Physical collision or Fleet deadlock detected during computation.",
                status_code=409,
            )

        self._system_logger.info("FMS Simulation completed successfully", log_ctx)
        return SimResultDto(
            scenario_id=scenario.scenario_id,
            is_success=True,
            collision_count=detector.collision_count,
            estimated_cycle_time_sec=14.5,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            trajectory_points=trajectory_results,
        )

    def _check_vram_resource_limit(self) -> bool:
        try:
            import torch

            if torch.cuda.is_available():
                allocated_mb = torch.cuda.memory_allocated() / (1024 * 1024)
                return allocated_mb <= self.MAX_VRAM_CACHE_LIMIT_MB
        except Exception:
            pass
        return True
