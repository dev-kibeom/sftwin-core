from typing import Any, Protocol


class ITurnkeyQuoteGateway(Protocol):
    """외부 B2B 공급망/제조사 원격 견적 산출 연동 포트"""

    def request_turnkey_quote(self, asset_ids: list[str]) -> dict[str, Any]:
        """외부 공급망 시스템에 턴키 견적 요청 API 호출"""
        ...
