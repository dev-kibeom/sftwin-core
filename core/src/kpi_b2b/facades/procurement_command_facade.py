from kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from kpi_b2b.b2b_procurement.application.layout_mirroring.layout_mirroring_usecase import (
    LayoutMirroringUseCase,
)
from kpi_b2b.b2b_procurement.application.process_production_order.process_production_order_usecase import (
    ProcessProductionOrderUseCase,
)
from kpi_b2b.b2b_procurement.application.process_production_order.production_order_request_dto import (
    ProductionOrderRequestDto,
)
from kpi_b2b.ports.inbound.dtos.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.ports.inbound.dtos.production_order_result_dto import (
    ProductionOrderResultDto,
)
from kpi_b2b.ports.inbound.dtos.session_data_dto import SessionDataDto
from kpi_b2b.ports.inbound.i_procurement_command_facade import (
    IProcurementCommandFacade,
)
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.ports.outbound.i_procurement_query_repository import (
    IProcurementQueryRepository,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.rbac_authorization_manager import RbacAuthorizationManager


class ProcurementCommandFacade(IProcurementCommandFacade):
    def __init__(
        self,
        generate_quote_uc: GenerateQuoteUseCase,
        mirroring_uc: LayoutMirroringUseCase,
        process_production_order_uc: ProcessProductionOrderUseCase,
        command_repo: IProcurementCommandRepository,
        query_repo: IProcurementQueryRepository,
        rbac_manager: RbacAuthorizationManager,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._generate_quote_uc = generate_quote_uc
        self._mirroring_uc = mirroring_uc
        self._process_production_order_uc = process_production_order_uc
        self._command_repo = command_repo
        self._query_repo = query_repo
        self._rbac_manager = rbac_manager
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="ProcurementCommandFacade"
        )

    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-B2B-FACADE"),
            context={"idempotency_key": idempotency_key, "user_id": ctx.user_id},
        )

        if idempotency_key:
            quote = self._query_repo.find_cached_quote(idempotency_key)
            if quote:
                self._system_logger.info(
                    "Idempotency Cache Hit. Returning cached quote.", log_ctx
                )
                return B2bQuoteDto(**quote)

        self._system_logger.info(
            "Cache Miss. Proceeding to generate new quote.", log_ctx
        )
        quote_dto = self._generate_quote_uc.execute(asset_ids=asset_ids, ctx=ctx)

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

        return self._mirroring_uc.execute(baseline_id=baseline_id, ctx=ctx)

    def process_production_order(
        self, request_dto: ProductionOrderRequestDto, ctx: UserContext
    ) -> ProductionOrderResultDto:
        return self._process_production_order_uc.execute(
            request_dto=request_dto, ctx=ctx
        )
