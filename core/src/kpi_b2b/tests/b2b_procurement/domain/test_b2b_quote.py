import pytest
from kpi_b2b.b2b_procurement.domain.b2b_quote.b2b_quote import B2bQuote
from kpi_b2b.b2b_procurement.domain.b2b_quote.b2b_quote_status_enum import (
    B2bQuoteStatus,
)


def test_tc_b2b_quote_factory_create_success():
    """팩토리 메서드를 통한 견적 생성 및 튜플 변환 검증"""
    quote = B2bQuote.create(
        asset_ids=["CNC-01", "ROBOT-01"],
        total_estimated_price=250000.0,
        delivery_days_estimated=10,
    )

    assert quote.quote_id.startswith("QT-")
    assert quote.asset_ids == ("CNC-01", "ROBOT-01")
    assert quote.total_estimated_price == 250000.0
    assert quote.delivery_days_estimated == 10
    assert quote.status == B2bQuoteStatus.REQUESTED


def test_tc_b2b_quote_accept_and_reject_lifecycle():
    """견적 승인/거절 상태 전이 및 중복 처리 차단 검증"""
    # 1. 견적 승인 전이
    quote_accept = B2bQuote.create(
        asset_ids=["CNC-01"],
        total_estimated_price=100.0,
        delivery_days_estimated=1,
    )
    quote_accept.accept()
    assert quote_accept.status == B2bQuoteStatus.ACCEPTED

    # 2. 승인된 견적 거절 시도 시 예외 검증
    with pytest.raises(ValueError, match="Cannot reject an already accepted quote"):
        quote_accept.reject()

    # 3. 견적 거절 전이
    quote_reject = B2bQuote.create(
        asset_ids=["CNC-01"],
        total_estimated_price=100.0,
        delivery_days_estimated=1,
    )
    quote_reject.reject(reason="Price too high")
    assert quote_reject.status == B2bQuoteStatus.REJECTED


def test_tc_b2b_quote_validation_invariants():
    """도메인 불변식 위반(빈 자산 목록, 음수 금액/납기일) 시 예외 검증"""
    with pytest.raises(ValueError, match="asset_ids cannot be empty"):
        B2bQuote(
            quote_id="QT-01",
            asset_ids=(),
            total_estimated_price=100.0,
            delivery_days_estimated=5,
        )

    with pytest.raises(ValueError, match="Total estimated price cannot be negative"):
        B2bQuote(
            quote_id="QT-01",
            asset_ids=("CNC-01",),
            total_estimated_price=-10.0,
            delivery_days_estimated=5,
        )

    with pytest.raises(ValueError, match="Delivery days estimated cannot be negative"):
        B2bQuote(
            quote_id="QT-01",
            asset_ids=("CNC-01",),
            total_estimated_price=100.0,
            delivery_days_estimated=-1,
        )
