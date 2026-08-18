from dataclasses import dataclass

from .b2b_quote_status_enum import B2bQuoteStatus


@dataclass(frozen=True)
class B2bQuote:
    """B2B 조달 턴키 견적 도메인 엔티티"""

    quote_id: str
    asset_ids: tuple[str, ...]
    total_estimated_price: float
    delivery_days_estimated: int
    scenario_id: str = "SCENARIO-DEFAULT"
    status: B2bQuoteStatus = B2bQuoteStatus.REQUESTED

    def __post_init__(self) -> None:
        if not self.quote_id or not self.quote_id.strip():
            raise ValueError("Valid quote_id is required.")
        if not self.asset_ids:
            raise ValueError("asset_ids cannot be empty for a B2B quote.")
        if self.total_estimated_price < 0:
            raise ValueError("Total estimated price cannot be negative.")
        if self.delivery_days_estimated < 0:
            raise ValueError("Delivery days estimated cannot be negative.")

    def accept(self) -> None:
        """견적 승인 및 발주 확정 전이"""
        if (
            self.status != B2bQuoteStatus.PROCESSED
            and self.status != B2bQuoteStatus.REQUESTED
        ):
            raise ValueError(f"Cannot accept quote in '{self.status.value}' state.")
        self.status = B2bQuoteStatus.ACCEPTED

    def reject(self, reason: str = "") -> None:
        """견적 거절 전이"""
        if self.status == B2bQuoteStatus.ACCEPTED:
            raise ValueError("Cannot reject an already accepted quote.")
        self.status = B2bQuoteStatus.REJECTED
