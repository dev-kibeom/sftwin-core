from typing import Any, Protocol

from kpi_b2b.b2b_procurement.domain.b2b_quote import B2bQuote
from kpi_b2b.b2b_procurement.domain.expert_session import ExpertSession


class IProcurementCommandRepository(Protocol):
    """
    B2B 조달 도메인 전용 쓰기(Command) 포트 (외부 B2B 연동, DB 영속화, 멱등성 캐시 저장)
    """

    def request_turnkey_quote(self, assets: list[str]) -> dict[str, Any]:
        """외부 B2B 공급망 턴키 견적 요청"""
        ...

    def save_quote(self, quote: B2bQuote) -> None:
        """견적 엔티티 영속화"""
        ...

    def save_expert_session(self, session: ExpertSession) -> None:
        """상담 세션 엔티티 영속화"""
        ...

    def save_cached_quote(
        self, idempotency_key: str, data: dict[str, Any], ttl_seconds: int = 86400
    ) -> None:
        """멱등성 캐시 저장"""
        ...
