from typing import Protocol

from kpi_b2b.b2b_procurement.application.process_production_order.production_order_request_dto import (
    ProductionOrderRequestDto,
)
from kpi_b2b.contracts.dtos.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.contracts.dtos.production_order_result_dto import (
    ProductionOrderResultDto,
)
from kpi_b2b.contracts.dtos.session_data_dto import SessionDataDto
from shared.context.user_context import UserContext


class IProcurementCommandFacade(Protocol):
    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto: ...

    def create_expert_session(
        self, baseline_id: str, ctx: UserContext
    ) -> SessionDataDto: ...

    def process_production_order(
        self, request_dto: ProductionOrderRequestDto, ctx: UserContext
    ) -> ProductionOrderResultDto: ...
