from digital_twin.ports.outbound.i_baseline_query_repository import (
    IBaselineQueryRepository,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context

from .asset_mapping_render_dto import AssetMappingRenderDto
from .layout_render_dto import LayoutRenderDto


class GetLayoutUseCase:
    def __init__(
        self,
        query_repo: IBaselineQueryRepository,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._query_repo = query_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GetLayoutUseCase"
        )

    @require_user_context
    def execute(self, baseline_id: str, ctx: UserContext) -> LayoutRenderDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-DEFAULT"),
            context={
                "baseline_id": baseline_id,
                "user_id": getattr(ctx, "user_id", "UNKNOWN"),
                "company_id": getattr(ctx, "company_id", "UNKNOWN"),
            },
        )

        self._system_logger.debug(
            f"Querying baseline layout: {baseline_id}", log_ctx=log_ctx
        )

        raw_data = self._query_repo.find_by_id(baseline_id)
        if not raw_data:
            self._system_logger.warn(
                f"Baseline layout not found: '{baseline_id}'",
                log_ctx=log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_TWIN_NOT_FOUND,
                message=f"Requested 3D baseline layout '{baseline_id}' does not exist.",
                status_code=404,
            )

        owner_company_id = raw_data.get("company_id", "")
        if not self._is_accessible(baseline_id, owner_company_id, ctx):
            self._system_logger.warn(
                f"Access denied for baseline '{baseline_id}' (Owner: {owner_company_id}, Requester: {ctx.company_id})",
                log_ctx=log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_TWIN_NOT_FOUND,
                message=f"Requested 3D baseline layout '{baseline_id}' does not exist.",
                status_code=404,
            )

        mappings_list = [
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
            for item in raw_data.get("asset_mappings", [])
        ]

        self._system_logger.info(
            f"Baseline layout '{baseline_id}' retrieved successfully",
            log_ctx=log_ctx,
        )

        return LayoutRenderDto(
            baseline_id=raw_data.get("baseline_id", baseline_id),
            baseline_name=raw_data.get("baseline_name", ""),
            company_id=owner_company_id,
            sync_error_rate=raw_data.get("sync_error_rate", 0.0),
            sync_status=raw_data.get("sync_status", "COMPLETED"),
            asset_mappings=mappings_list,
        )

    def _is_accessible(
        self, baseline_id: str, owner_company_id: str, ctx: UserContext
    ) -> bool:
        if ctx.accessible_factory_ids and baseline_id in ctx.accessible_factory_ids:
            return True
        return bool(
            owner_company_id and ctx.company_id and owner_company_id == ctx.company_id
        )
