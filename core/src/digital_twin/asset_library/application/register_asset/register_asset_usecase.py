from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.ports.inbound.dtos.asset_dto import AssetDto
from digital_twin.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class RegisterAssetUseCase:
    def __init__(
        self,
        command_repo: IAssetCommandRepository,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._command_repo = command_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="RegisterAssetUseCase"
        )

    @require_user_context
    def execute(self, asset_dto: AssetDto, ctx: UserContext) -> str:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-DEFAULT"),
            context={
                "asset_name": asset_dto.asset_name,
                "asset_type": asset_dto.asset_type,
                "user_id": ctx.user_id,
                "company_id": ctx.company_id,
            },
        )
        self._system_logger.debug(f"Executing {self.__class__.__name__}", log_ctx)

        try:
            asset_enum = AssetType(asset_dto.asset_type)
            domain_entity = Asset(
                asset_name=asset_dto.asset_name,
                asset_type=asset_enum,
                company_id=ctx.company_id,
                kinematics_metadata=asset_dto.kinematics_metadata or {},
                cad_file_path=asset_dto.cad_file_path,
                created_by=ctx.username,
                updated_by=ctx.username,
            )
        except ValueError as e:
            self._system_logger.warn(
                f"Asset domain validation failed: {str(e)}", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=str(e),
                details={"invalid_input": asset_dto.asset_name},
            ) from e

        try:
            saved_entity = self._command_repo.save(domain_entity)
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error(
                "Database persistence failed during asset registration.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
            ) from e

        log_ctx.context["asset_id"] = saved_entity.asset_id
        self._system_logger.info(
            f"Asset '{saved_entity.asset_id}' registered successfully",
            log_ctx,
        )

        return saved_entity.asset_id
