"""
[File Summary]
RunFmsSimulationUseCase (Stateless Singleton)
FMS 시뮬레이션 가동 흐름을 오케스트레이션합니다.
"""

from datetime import datetime, timezone
from typing import Any

from src.shared.dtos.log_dtos import LogContext
from src.shared.dtos.sim_result_dto import SimResultDto
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.logger.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext
from src.simulation.fms_execution.domain.collision_detector import CollisionDetector
from src.simulation.fms_execution.domain.fms_scenario import FmsScenario


class RunFmsSimulationUseCase:
    MAX_VRAM_CACHE_LIMIT_MB = 4200.0

    def __init__(self, physics_adapter: Any, logger: GlobalSystemLogger | None = None):
        self._physics_adapter = physics_adapter
        self._logger = logger or GlobalSystemLogger(
            component_name="RunFmsSimulationUseCase"
        )

    def execute(
        self,
        scenario_id: str,
        baseline_id: str,
        assets: list[dict[str, Any]],
        ctx: UserContext,
    ) -> SimResultDto:
        log_ctx = LogContext(trace_id=f"TRC-{scenario_id}")
        self._logger.info(
            f"FMS Simulation execution requested by {ctx.user_id}", log_ctx
        )

        scenario = FmsScenario(
            scenario_id=scenario_id, baseline_id=baseline_id, assets=assets
        )
        if not scenario.validate_scenario():
            self._logger.warn("Invalid scenario metadata", log_ctx)
            raise BaseSystemException(
                error_code="ERR_SIM_INVALID_SCENARIO",
                message="AAS or Kinematics metadata schema violation or missing baseline_id.",
                status_code=400,
            )

        if not self._check_vram_resource_limit():
            self._logger.error("VRAM Resource exhausted over 4.2GB limit", log_ctx)
            raise BaseSystemException(
                error_code="ERR_SIM_RESOURCE_EXHAUSTED",
                message="GPU VRAM cache exceeds the 4.2GB limit. Request rejected to prevent OOM.",
                status_code=503,
            )

        try:
            trajectory_results = self._physics_adapter.calculate_kinematics(scenario)
        except TimeoutError as exc:
            self._logger.error("IPC Sync timeout (>1ms)", log_ctx, exc=exc)
            raise BaseSystemException(
                error_code="ERR_SIM_IPC_TIMEOUT",
                message="POSIX Shared Memory IPC synchronization timeout exceeded 1ms.",
                status_code=500,
            )

        detector = CollisionDetector()
        if detector.detect(trajectory_results):
            self._logger.warn(
                f"Collision/Deadlock detected. Count: {detector.collision_count}",
                log_ctx,
            )
            raise BaseSystemException(
                error_code="ERR_SIM_COLLISION_DETECTED",
                message="Physical collision or Fleet deadlock detected during computation.",
                status_code=409,
            )

        self._logger.info("FMS Simulation completed successfully", log_ctx)
        return SimResultDto(
            scenario_id=scenario_id,
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
