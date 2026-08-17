from digital_twin.asset_library.domain.asset import Asset
from digital_twin.asset_library.domain.enums.asset_type_enum import AssetTypeEnum
from digital_twin.ports.inbound.dtos.asset_dto import AssetDto
from digital_twin.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class RegisterAssetUseCase:
    def __init__(
        self,
        command_repo: IAssetCommandRepository,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._command_repo = command_repo
        self._logger = logger or GlobalSystemLogger(
            component_name="RegisterAssetUseCase"
        )

    @require_user_context
    def execute(self, asset_dto: AssetDto, ctx: UserContext) -> str:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-DEFAULT"),
            context={
                "asset_name": asset_dto.asset_name,
                "asset_type": asset_dto.asset_type,
                "user_id": getattr(ctx, "user_id", "UNKNOWN"),
                "company_id": getattr(ctx, "company_id", "UNKNOWN"),
            },
        )

        try:
            asset_enum = AssetTypeEnum(asset_dto.asset_type)
        except ValueError as e:
            self._logger.warn(
                f"Invalid asset type: {asset_dto.asset_type}",
                log_ctx=LogContext(
                    trace_id=log_ctx.trace_id,
                    context=log_ctx.context,
                    exc=e,
                ),
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_TWIN_INVALID_SCHEMA,
                message=f"Invalid asset type '{asset_dto.asset_type}'.",
                status_code=400,
                details={"asset_type": asset_dto.asset_type},
            ) from e

        domain_entity = Asset(
            asset_name=asset_dto.asset_name,
            asset_type=asset_enum,
            company_id=ctx.company_id,
            kinematics_metadata=asset_dto.kinematics_metadata or {},
            cad_file_path=asset_dto.cad_file_path,
            created_by=ctx.username,
            updated_by=ctx.username,
        )

        domain_entity.validate_schema()
        saved_entity = self._command_repo.save(domain_entity)

        log_ctx.context["asset_id"] = saved_entity.asset_id
        self._logger.info(
            f"Asset '{saved_entity.asset_id}' registered successfully",
            log_ctx=log_ctx,
        )

        return saved_entity.asset_id
