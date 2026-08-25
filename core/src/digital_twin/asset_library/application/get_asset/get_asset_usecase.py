from digital_twin.contracts.dtos.asset_dto import AssetDetailDto
from digital_twin.contracts.ports.outbound.i_asset_query_repository import (
    IAssetQueryRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class GetAssetUseCase:
    """자산 단건 조회 UseCase"""

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
    def execute(self, asset_id: str, ctx: UserContext) -> AssetDetailDto:
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

        self._system_logger.info(
            f"Asset '{asset_id}' retrieved successfully",
            extra={"asset_id": asset_id},
        )
        return dto
