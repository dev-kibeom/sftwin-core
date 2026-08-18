from kpi_b2b.b2b_procurement.domain.expert_session import ExpertSession
from kpi_b2b.ports.inbound.dtos.session_data_dto import SessionDataDto
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class LayoutMirroringUseCase:
    def __init__(
        self,
        command_repo: IProcurementCommandRepository,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._command_repo = command_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="LayoutMirroringUseCase"
        )

    @require_user_context
    def execute(self, baseline_id: str, ctx: UserContext) -> SessionDataDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-MIRRORING"),
            context={"baseline_id": baseline_id, "company_id": ctx.company_id},
        )

        try:
            session_entity = ExpertSession.create_new_session(baseline_id=baseline_id)
        except ValueError as e:
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                message=str(e),
                status_code=400,
            ) from e

        try:
            self._command_repo.save_expert_session(session_entity)
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error(
                "Database persistence failed during expert session creation.", log_ctx
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR,
                message="시스템 내부 장애가 발생했습니다. 잠시 후 다시 시도해주세요.",
                status_code=500,
            ) from e

        self._system_logger.info(
            f"Successfully generated expert session: {session_entity.session_id}",
            log_ctx,
        )

        return SessionDataDto(
            session_id=session_entity.session_id,
            session_token=session_entity.session_token,
            status=session_entity.status.value,
            expires_in_seconds=14400,
        )
