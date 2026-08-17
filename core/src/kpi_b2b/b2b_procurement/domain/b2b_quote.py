import uuid
from dataclasses import dataclass

from .enums.b2b_quote_status_enum import B2bQuoteStatusEnum


@dataclass
class B2bQuote:
    quote_id: str
    scenario_id: str
    total_estimated_price: float
    status: B2bQuoteStatusEnum
    delivery_days_estimated: int

    @classmethod
    def create_new_quote(
        cls, assets: list[str], total_price: float, days: int
    ) -> "B2bQuote":
        """외부 API 반환 데이터를 바탕으로 신규 견적 엔티티를 생성하고 REQUESTED 상태를 강제합니다."""
        return cls(
            quote_id=f"QT-{uuid.uuid4()}",
            scenario_id="SCENARIO-DEFAULT",  # FMS 시나리오 ID (현재는 기본값)
            total_estimated_price=total_price,
            status=B2bQuoteStatusEnum.REQUESTED,
            delivery_days_estimated=days,
        )
