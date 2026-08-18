from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context
from simulation.layout_optimization.application.optimize_layout.optimize_layout_dto import (
    OptimizeLayoutRequestDto,
)
from simulation.layout_optimization.domain.layout_optimizer.layout_optimizer import (
    LayoutOptimizer,
)
from simulation.ports.inbound.dtos.optimized_asset_placement_dto import (
    OptimizedAssetPlacementDto,
)


class OptimizeLayoutUseCase:
    def __init__(self, system_logger: GlobalSystemLogger | None = None):
        self._optimizer = LayoutOptimizer()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="OptimizeLayoutUseCase"
        )

    @require_user_context
    def execute(
        self, request_dto: OptimizeLayoutRequestDto, ctx: UserContext
    ) -> list[OptimizedAssetPlacementDto]:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", f"TRC-LAYOUT-{ctx.user_id}"),
            context={"user_id": ctx.user_id, "company_id": ctx.company_id},
        )
        self._system_logger.debug(f"Executing {self.__class__.__name__}", log_ctx)

        try:
            placements = self._optimizer.optimize_placement(
                request_dto.assets, request_dto.canvas_bounds
            )
        except ValueError as e:
            self._system_logger.warn(
                f"Layout optimization failed validation: {str(e)}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        self._system_logger.info(
            f"Successfully calculated {len(placements)} asset placements", log_ctx
        )

        return [
            OptimizedAssetPlacementDto(
                asset_id=p.asset_id,
                pos_x=p.pos_x,
                pos_y=p.pos_y,
                pos_z=p.pos_z,
                rotation_yaw=p.rotation_yaw,
            )
            for p in placements
        ]
