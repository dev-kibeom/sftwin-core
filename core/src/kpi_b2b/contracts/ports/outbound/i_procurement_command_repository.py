from typing import Protocol

from kpi_b2b.b2b_procurement.domain.b2b_quote.b2b_quote import B2bQuote
from kpi_b2b.b2b_procurement.domain.expert_session.expert_session import (
    ExpertSession,
)
from kpi_b2b.b2b_procurement.domain.production_order.production_order import (
    ProductionOrder,
)


class IProcurementCommandRepository(Protocol):
    """B2B 조달 및 발주 도메인 엔티티 영속화(CUD) 전용 포트"""

    def save_quote(self, quote: B2bQuote) -> None:
        """견적 엔티티 저장"""
        ...

    def save_expert_session(self, session: ExpertSession) -> None:
        """상담 세션 엔티티 저장"""
        ...

    def save_production_order(self, order: ProductionOrder) -> None:
        """생산 발주 엔티티 저장"""
        ...
