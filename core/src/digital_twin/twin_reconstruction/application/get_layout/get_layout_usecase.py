from digital_twin.ports.outbound.i_baseline_query_repository import (
    IBaselineQueryRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context

from .layout_render_dto import LayoutRenderDto
from .layout_render_mapper import LayoutRenderMapper


class GetLayoutUseCase:
    """3D 베이스라인 레이아웃 및 핫스팟 시각화 데이터를 조회하는 유스케이스"""

    def __init__(
        self,
        query_repo: IBaselineQueryRepository,
        mapper: LayoutRenderMapper | None = None,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._query_repo = query_repo
        self._mapper = mapper or LayoutRenderMapper()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GetLayoutUseCase"
        )

    @require_user_context
    def execute(self, baseline_id: str, ctx: UserContext) -> LayoutRenderDto:
        # 1. 테넌시/삭제 필터링이 포함된 DTO 단건 조회
        baseline_dto = self._query_repo.find_by_id(
            baseline_id=baseline_id,
            company_id=ctx.company_id,
        )

        if not baseline_dto:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_NOT_FOUND,
                custom_message=(
                    f"Requested 3D baseline layout '{baseline_id}' does not exist or access is denied."
                ),
            )

        # 2. 전용 Mapper를 통한 렌더링 DTO 조립
        response_dto = self._mapper.to_render_dto(baseline_dto)

        # 3. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Baseline layout '{baseline_id}' with {len(response_dto.asset_mappings)} rendered assets retrieved successfully",
            extra={
                "baseline_id": baseline_id,
                "rendered_assets_count": len(response_dto.asset_mappings),
            },
        )

        return response_dto
