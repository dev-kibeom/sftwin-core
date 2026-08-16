from typing import Any

from shared.context.log_context import LogContext
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.context.user_context import UserContext
from simulation.layout_optimization.domain.layout_optimizer import (
    LayoutOptimizer,
    OptimizedAssetPlacement,
)


class OptimizeLayoutUseCase:
    def __init__(self, logger: GlobalSystemLogger | None = None):
        self._optimizer = LayoutOptimizer()
        self._logger = logger or GlobalSystemLogger(
            component_name="OptimizeLayoutUseCase"
        )

    def execute(
        self,
        assets: list[dict[str, Any]],
        canvas_bounds: dict[str, float],
        ctx: UserContext,
    ) -> list[OptimizedAssetPlacement]:
        log_ctx = LogContext(trace_id=f"TRC-LAYOUT-{ctx.user_id}")
        self._logger.info(f"Layout optimization requested by {ctx.user_id}", log_ctx)

        placements = self._optimizer.optimize_placement(assets, canvas_bounds)
        self._logger.info(
            f"Successfully calculated {len(placements)} asset placements", log_ctx
        )
        return placements
