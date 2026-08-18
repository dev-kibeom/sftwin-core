from digital_twin.ports.inbound.dtos.asset_dto import AssetDto
from digital_twin.ports.outbound.i_asset_query_repository import IAssetQueryRepository
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_exception import BaseSystemException
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
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-DEFAULT"),
            context={
                "asset_id": asset_id,
                "user_id": getattr(ctx, "user_id", "UNKNOWN"),
                "company_id": getattr(ctx, "company_id", "UNKNOWN"),
            },
        )

        self._system_logger.debug(f"Querying asset: {asset_id}", log_ctx=log_ctx)

        entity = self._query_repo.find_by_id(asset_id)

        if not entity or entity.is_deleted or entity.company_id != ctx.company_id:
            self._system_logger.warn(
                f"Asset query failed - not found or unauthorized: {asset_id}",
                log_ctx=log_ctx,
            )

            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_TWIN_NOT_FOUND,
                message=f"Requested asset '{asset_id}' does not exist.",
                status_code=404,
            )

        self._system_logger.info(
            f"Asset '{asset_id}' retrieved successfully", log_ctx=log_ctx
        )

        return AssetDto(
            asset_id=entity.asset_id,
            asset_name=entity.asset_name,
            asset_type=entity.asset_type.value,
            cad_file_path=entity.cad_file_path,
            kinematics_metadata=entity.kinematics_metadata,
            created_at=entity.created_at,
        )
