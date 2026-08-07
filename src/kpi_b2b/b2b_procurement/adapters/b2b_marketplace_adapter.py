"""
@file b2b_marketplace_adapter.py
@description 외부 시스템과의 HTTP 통신을 담당하는 BaseB2bMarketplacePort 구현체
"""

from typing import Any

from .base_b2b_marketplace_port import BaseB2bMarketplacePort


class B2bMarketplaceAdapter(BaseB2bMarketplacePort):
    def __init__(self, api_client: Any):
        self._api_client = api_client

    def request_turnkey_quote(self, assets: list[str]) -> dict[str, Any]:
        # 실제 환경에서는 self._api_client.post("...", json={"assets": assets}) 호출
        raise NotImplementedError("Real HTTP requests are implemented here.")
