from typing import Protocol

from kpi_b2b.b2b_procurement.application.generate_quote.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.b2b_procurement.application.layout_mirroring.session_data_dto import (
    SessionDataDto,
)
from shared.security.user_context import UserContext


class IProcurementCommandFacade(Protocol):
    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto: ...

    def create_expert_session(
        self, baseline_id: str, ctx: UserContext
    ) -> SessionDataDto: ...
