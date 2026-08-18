import uuid

from kpi_b2b.b2b_procurement.domain.expert_session.expert_session import (
    ExpertSession,
)
from kpi_b2b.ports.inbound.dtos.session_data_dto import SessionDataDto
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.ports.outbound.i_procurement_query_repository import (
    IProcurementQueryRepository,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class CreateExpertSessionUseCase:
    def __init__(
        self,
        command_repo: IProcurementCommandRepository,
        query_repo: IProcurementQueryRepository,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._command_repo = command_repo
        self._query_repo = query_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="CreateExpertSessionUseCase"
        )

    @require_user_context
    def execute(self, baseline_id: str, ctx: UserContext) -> SessionDataDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-MIRRORING"),
            context={"baseline_id": baseline_id, "company_id": ctx.company_id},
        )

        try:
            owner_id = self._query_repo.get_baseline_owner(baseline_id)
            if not owner_id or owner_id != ctx.company_id:
                self._system_logger.warn(
                    f"Baseline not found or unauthorized access attempt: '{baseline_id}' by tenant '{ctx.company_id}'",
                    log_ctx,
                )
                raise BaseSystemException.from_error_code(
                    GlobalErrorCode.ERR_TWIN_NOT_FOUND,
                    custom_message=f"Digital twin baseline '{baseline_id}' does not exist or access is forbidden.",
                )
        except BaseSystemException:
            raise
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error(
                "Failed to query baseline owner during session creation.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
            ) from e

        try:
            session_entity = ExpertSession(
                session_id=f"SESS-{uuid.uuid4()}",
                baseline_id=baseline_id,
                session_token=f"TKN-{uuid.uuid4().hex}",
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        try:
            self._command_repo.save_expert_session(session_entity)
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error(
                "Database persistence failed during expert session creation.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
            ) from e

        self._system_logger.info(
            f"Successfully created expert session: {session_entity.session_id}",
            log_ctx,
        )

        return SessionDataDto(
            session_id=session_entity.session_id,
            session_token=session_entity.session_token,
            status=session_entity.status.value,
            expires_in_seconds=session_entity.expires_in_seconds,
        )
