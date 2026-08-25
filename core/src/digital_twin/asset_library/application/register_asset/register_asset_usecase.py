from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.contracts.dtos.asset_dto import AssetDetailDto
from digital_twin.contracts.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class RegisterAssetUseCase:
    """신규 자산 등록 UseCase"""

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
    def execute(self, asset_dto: AssetDetailDto, ctx: UserContext) -> str:
        try:
            asset_type_enum = AssetType(asset_dto.asset_type)
            asset = Asset(
                asset_name=asset_dto.asset_name,
                asset_type=asset_type_enum,
                company_id=ctx.company_id,
                kinematics_metadata=asset_dto.kinematics_metadata or {},
                cad_file_path=asset_dto.cad_file_path,
                submodels=asset_dto.submodels or {},
                created_by=ctx.user_id,
                updated_by=ctx.user_id,
            )
        except (ValueError, KeyError) as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=str(e),
                details={"asset_name": asset_dto.asset_name},
            ) from e

        # 영속화 수행 (save는 None 반환)
        self._command_repo.save(asset)

        self._system_logger.info(
            f"Asset '{asset.asset_id}' registered successfully",
            extra={
                "asset_id": asset.asset_id,
                "asset_name": asset.asset_name,
            },
        )
        return asset.asset_id
