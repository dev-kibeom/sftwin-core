from digital_twin.ports.outbound.i_baseline_query_repository import (
    IBaselineQueryRepository,
)
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext

from .asset_mapping_render_dto import AssetMappingRenderDto
from .layout_render_dto import LayoutRenderDto


class GetLayoutUseCase:
    def __init__(
        self,
        query_repo: IBaselineQueryRepository,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._query_repo = query_repo
        self._logger = logger or GlobalSystemLogger(component_name="GetLayoutUseCase")

    def execute(self, baseline_id: str, ctx: UserContext) -> LayoutRenderDto:
        if not ctx:
            self._logger.error("[GetLayoutUseCase] UserContext missing")
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="UserContext is required for authorization.",
                status_code=400,
            )

        raw_data = self._query_repo.find_by_id(baseline_id)

        if not raw_data:
            self._logger.warn(
                f"[GetLayoutUseCase] Baseline layout not found: '{baseline_id}'"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_NOT_FOUND,
                message=f"Requested 3D baseline layout '{baseline_id}' does not exist.",
                status_code=404,
            )

        owner_company_id = raw_data.get("company_id", "")
        if not self.verify_access_rights(baseline_id, owner_company_id, ctx):
            self._logger.warn(
                f"[GetLayoutUseCase] Access denied for baseline_id='{baseline_id}'. "
                f"Owner company='{owner_company_id}', Request company='{ctx.company_id}'"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_NOT_FOUND,
                message=f"Requested 3D baseline layout '{baseline_id}' does not exist.",
                status_code=404,
            )

        mappings_list: list[AssetMappingRenderDto] = []
        for item in raw_data.get("asset_mappings", []):
            mappings_list.append(
                AssetMappingRenderDto(
                    asset_id=item.get("asset_id", ""),
                    asset_name=item.get("asset_name", ""),
                    asset_type=item.get("asset_type", "UNKNOWN"),
                    cad_file_path=item.get("cad_file_path"),
                    position_xyz_json=item.get(
                        "position_xyz_json", {"x": 0.0, "y": 0.0, "z": 0.0}
                    ),
                    rotation_q_json=item.get(
                        "rotation_q_json", {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
                    ),
                )
            )

        return LayoutRenderDto(
            baseline_id=raw_data.get("baseline_id", baseline_id),
            baseline_name=raw_data.get("baseline_name", ""),
            company_id=owner_company_id,
            sync_error_rate=raw_data.get("sync_error_rate", 0.0),
            sync_status=raw_data.get("sync_status", "COMPLETED"),
            asset_mappings=mappings_list,
        )

    def verify_access_rights(
        self, baseline_id: str, owner_company_id: str, ctx: UserContext
    ) -> bool:
        if ctx.accessible_factory_ids and baseline_id in ctx.accessible_factory_ids:
            return True

        return bool(
            owner_company_id and ctx.company_id and owner_company_id == ctx.company_id
        )
