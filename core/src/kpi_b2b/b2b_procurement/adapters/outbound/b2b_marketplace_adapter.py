"""
@file b2b_marketplace_adapter.py
@description 외부 시스템과의 통신을 담당하는 BaseB2bMarketplacePort 구현체
"""

from typing import Any

from shared.dtos.log_dtos import LogContext
from shared.logger.global_system_logger import GlobalSystemLogger

from kpi_b2b.b2b_procurement.ports.outbound.base_b2b_marketplace import (
    BaseB2bMarketplacePort,
)


class B2bMarketplaceAdapter(BaseB2bMarketplacePort):
    def __init__(
        self, api_client: Any = None, logger: GlobalSystemLogger | None = None
    ):
        self._api_client = api_client
        self._logger = logger or GlobalSystemLogger(
            component_name="B2bMarketplaceAdapter"
        )

    def request_turnkey_quote(self, assets: list[str]) -> dict[str, Any]:
        log_ctx = LogContext(context={"asset_count": len(assets)})
        self._logger.info(
            f"Requesting B2B Turnkey quote for {len(assets)} assets.", log_ctx
        )

        estimated_unit_price = 15000000.0
        total_price = float(len(assets) * estimated_unit_price)

        return {
            "total_estimated_price": total_price,
            "delivery_days_estimated": 14,
            "currency": "KRW",
            "status": "PROCESSED",
        }
