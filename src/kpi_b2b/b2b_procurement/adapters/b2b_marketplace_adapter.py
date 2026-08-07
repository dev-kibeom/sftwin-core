"""
@file b2b_marketplace_adapter.py
@description 외부 시스템과의 통신을 담당하는 BaseB2bMarketplacePort 구현체
"""

import logging
from typing import Any

from .base_b2b_marketplace_port import BaseB2bMarketplacePort

logger = logging.getLogger("kpi_b2b.b2b_marketplace_adapter")


class B2bMarketplaceAdapter(BaseB2bMarketplacePort):
    def __init__(self, api_client: Any = None):
        self._api_client = api_client

    def request_turnkey_quote(self, assets: list[str]) -> dict[str, Any]:
        logger.info(f"Requesting B2B Turnkey quote for {len(assets)} assets.")

        # 외부 B2B 마켓플레이스 공급망 견적 산출 연산 (데모/PoC 스코프 견적)
        estimated_unit_price = 15000000.0  # 자산당 평균 1,500만원
        total_price = float(len(assets) * estimated_unit_price)

        return {
            "total_estimated_price": total_price,
            "delivery_days_estimated": 14,
            "currency": "KRW",
            "status": "PROCESSED",
        }
