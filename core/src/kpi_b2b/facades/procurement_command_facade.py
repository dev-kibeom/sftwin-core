from kpi_b2b.b2b_procurement.application.create_expert_session.create_expert_session_usecase import (
    CreateExpertSessionUseCase,
)
from kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from kpi_b2b.b2b_procurement.application.process_production_order.process_production_order_usecase import (
    ProcessProductionOrderUseCase,
)
from kpi_b2b.b2b_procurement.application.process_production_order.production_order_request_dto import (
    ProductionOrderRequestDto,
)
from kpi_b2b.contracts.dtos.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.contracts.dtos.production_order_result_dto import (
    ProductionOrderResultDto,
)
from kpi_b2b.contracts.dtos.session_data_dto import SessionDataDto
from kpi_b2b.contracts.ports.inbound.i_procurement_command_facade import (
    IProcurementCommandFacade,
)
from shared.context.user_context import UserContext
from shared.security.rbac_authorization_manager import RbacAuthorizationManager


class ProcurementCommandFacade(IProcurementCommandFacade):
    def __init__(
        self,
        generate_quote_uc: GenerateQuoteUseCase,
        create_expert_session_uc: CreateExpertSessionUseCase,
        process_production_order_uc: ProcessProductionOrderUseCase,
        rbac_manager: RbacAuthorizationManager | None = None,
    ):
        self._generate_quote_uc = generate_quote_uc
        self._create_expert_session_uc = create_expert_session_uc
        self._process_production_order_uc = process_production_order_uc
        self._rbac_manager = rbac_manager

    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto:
        return self._generate_quote_uc.execute(
            asset_ids=asset_ids,
            ctx=ctx,
            idempotency_key=idempotency_key,
        )

    def create_expert_session(
        self, baseline_id: str, ctx: UserContext
    ) -> SessionDataDto:
        return self._create_expert_session_uc.execute(
            baseline_id=baseline_id,
            ctx=ctx,
        )

    def process_production_order(
        self, request_dto: ProductionOrderRequestDto, ctx: UserContext
    ) -> ProductionOrderResultDto:
        return self._process_production_order_uc.execute(
            request_dto=request_dto,
            ctx=ctx,
        )
