"""
@file base_b2b_marketplace.py
@description 의존성 역전 원칙(DIP)을 위한 외부 마켓플레이스 연동 추상 포트
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseB2bMarketplacePort(ABC):
    @abstractmethod
    def request_turnkey_quote(self, assets: list[str]) -> dict[str, Any]:
        """주어진 자산 목록으로 외부 B2B 마켓플레이스에 턴키 견적을 요청합니다."""
        pass
