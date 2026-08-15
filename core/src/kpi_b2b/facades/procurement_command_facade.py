"""
@file procurement_command_facade.py
@description RbacAuthorizationManager를 연동한 B2B 및 상담 세션 커맨드 파사드
"""

from kpi_b2b.b2b_procurement.application.generate_quote.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from kpi_b2b.b2b_procurement.application.layout_mirroring.layout_mirroring_usecase import (
    LayoutMirroringUseCase,
)
from kpi_b2b.b2b_procurement.application.layout_mirroring.session_data_dto import (
    SessionDataDto,
)
from kpi_b2b.ports.inbound.i_procurement_command_facade import IProcurementCommandFacade
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.ports.outbound.i_procurement_query_repository import (
    IProcurementQueryRepository,
)
from shared.logger.system_logger.log_context import LogContext
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.security.rbac_authorization_manager import RbacAuthorizationManager
from shared.security.user_context import UserContext


class ProcurementCommandFacade(IProcurementCommandFacade):
    def __init__(
        self,
        generate_quote_uc: GenerateQuoteUseCase,
        mirroring_uc: LayoutMirroringUseCase,
        command_repo: IProcurementCommandRepository,
        query_repo: IProcurementQueryRepository,
        rbac_manager: RbacAuthorizationManager,
        logger: GlobalSystemLogger | None = None,
    ):
        self._generate_quote_uc = generate_quote_uc
        self._mirroring_uc = mirroring_uc
        self._command_repo = command_repo
        self._query_repo = query_repo
        self._rbac_manager = rbac_manager
        self._logger = logger or GlobalSystemLogger(
            component_name="B2B_GenerateQuote_UseCase"
        )

    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto:
        log_ctx = LogContext(
            context={"idempotency_key": idempotency_key, "user_id": ctx.user_id}
        )

        if idempotency_key:
            quote = self._query_repo.find_cached_quote(idempotency_key)
            if quote:
                self._logger.info(
                    "Idempotency Cache Hit. Returning cached quote.", log_ctx
                )
                return B2bQuoteDto(**quote)

        self._logger.info("Cache Miss. Proceeding to generate new quote.", log_ctx)
        quote_dto = self._generate_quote_uc.execute(
            asset_ids=asset_ids, company_id=ctx.company_id
        )

        if idempotency_key:
            self._command_repo.save_cached_quote(idempotency_key, quote_dto.__dict__)

        return quote_dto

    def create_expert_session(
        self, baseline_id: str, ctx: UserContext
    ) -> SessionDataDto:
        target_company_id = (
            self._query_repo.get_baseline_owner(baseline_id) or "UNAUTHORIZED_TENANT"
        )

        self._rbac_manager.validate_company_isolation(
            user_ctx=ctx,
            target_company_id=target_company_id,
            target_resource=f"BASELINE:{baseline_id}",
        )

        return self._mirroring_uc.execute(
            baseline_id=baseline_id, company_id=ctx.company_id
        )
