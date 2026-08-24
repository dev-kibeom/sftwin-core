from digital_twin.contracts.dtos.asset_dto import AssetDto
from digital_twin.contracts.ports.outbound.i_asset_query_repository import (
    IAssetQueryRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class GetAssetUseCase:
    def __init__(
        self,
        query_repo: IAssetQueryRepository,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._query_repo = query_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GetAssetUseCase"
        )

    @require_user_context
    def execute(self, asset_id: str, ctx: UserContext) -> AssetDto:
        # 1. 테넌시/삭제 필터링이 포함된 DTO 직접 조회
        dto = self._query_repo.find_by_id(
            asset_id=asset_id,
            company_id=ctx.company_id,
        )

        if not dto:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_NOT_FOUND,
                custom_message=(
                    f"Requested asset '{asset_id}' does not exist or access is denied."
                ),
            )

        # 2. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Asset '{asset_id}' retrieved successfully",
            extra={"asset_id": asset_id},
        )

        return dto
