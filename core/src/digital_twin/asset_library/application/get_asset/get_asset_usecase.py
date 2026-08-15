from digital_twin.ports.outbound.i_asset_query_repository import IAssetQueryRepository
from shared.dtos.asset_dto import AssetDto
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext


class GetAssetUseCase:
    def __init__(
        self,
        query_repo: IAssetQueryRepository,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._query_repo = query_repo
        self._logger = logger or GlobalSystemLogger(component_name="GetAssetUseCase")

    def execute(self, asset_id: str, ctx: UserContext) -> AssetDto:
        entity = self._query_repo.find_by_id(asset_id)

        if not entity or entity.is_deleted or entity.company_id != ctx.company_id:
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_NOT_FOUND,
                message=f"Requested asset '{asset_id}' does not exist.",
                status_code=404,
            )

        return AssetDto(
            asset_id=entity.asset_id,
            asset_name=entity.asset_name,
            asset_type=entity.asset_type.value,
            cad_file_path=entity.cad_file_path,
            kinematics_metadata=entity.kinematics_metadata,
            created_at=entity.created_at,
        )
