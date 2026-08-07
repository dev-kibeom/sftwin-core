"""
@file b2b_quote.py
@description 발주 총액, 납기일, 상태 등을 캡슐화한 순수 B2B 견적 도메인 엔티티
"""

import uuid
from dataclasses import dataclass
from enum import Enum


class B2bQuoteStatusEnum(str, Enum):
    REQUESTED = "REQUESTED"  # 견적 요청 완료 및 대기 중
    PROCESSED = "PROCESSED"  # 공급사 견적 산출 완료
    ACCEPTED = "ACCEPTED"  # 발주 확정 (결제 완료)
    REJECTED = "REJECTED"  # 견적 거절 또는 취소


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
