from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context
from simulation.contracts.dtos.optimized_asset_placement_dto import (
    OptimizedAssetPlacementDto,
)
from simulation.layout_optimization.application.optimize_layout.optimize_layout_request_dto import (
    OptimizeLayoutRequestDto,
)
from simulation.layout_optimization.application.optimize_layout.optimized_layout_mapper import (
    OptimizedLayoutMapper,
)
from simulation.layout_optimization.domain.layout_optimizer.layout_optimizer import (
    LayoutOptimizer,
)


class OptimizeLayoutUseCase:
    """작업 공간 제약 조건에 따른 설비 3D 배치 최적화를 처리하는 유스케이스"""

    def __init__(
        self,
        mapper: OptimizedLayoutMapper | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._mapper = mapper or OptimizedLayoutMapper()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="OptimizeLayoutUseCase"
        )

    @require_user_context
    def execute(
        self,
        request_dto: OptimizeLayoutRequestDto,
        ctx: UserContext,
    ) -> list[OptimizedAssetPlacementDto]:
        # 1. DTO -> 도메인 명세 VO 변환 및 불변식 검증
        try:
            specs, bounds = self._mapper.to_domain_specs(
                request_dto.assets, request_dto.canvas_bounds
            )
            placements = LayoutOptimizer.optimize_placement(specs, bounds)
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        # 2. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Successfully calculated {len(placements)} asset placements for company: {ctx.company_id}",
            extra={
                "asset_count": len(placements),
                "company_id": ctx.company_id,
                "canvas_max_x": bounds.max_x,
            },
        )

        # 3. DTO 변환 및 반환
        return self._mapper.to_dto_list(placements)
