from digital_twin.asset_library.domain.asset import Asset
from digital_twin.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.dtos.asset_dto import AssetDto
from shared.enums.asset_type_enum import AssetTypeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext


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

    def execute(self, asset_dto: AssetDto, ctx: UserContext) -> str:
        if not ctx or not ctx.company_id:
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="UserContext with valid company_id is required.",
                status_code=400,
            )

        try:
            asset_enum = AssetTypeEnum(asset_dto.asset_type)
        except ValueError as e:
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_INVALID_SCHEMA,
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

        self._logger.info(f"{saved_entity.asset_id} registered successfully")

        return saved_entity.asset_id
