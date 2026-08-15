from typing import Any, Protocol


class IProcurementQueryRepository(Protocol):
    """
    B2B 조달 도메인 전용 읽기(Query) 포트 (멱등성 캐시 조회, 베이스라인 소유주 조회)
    """

    def find_cached_quote(self, idempotency_key: str) -> dict[str, Any] | None:
        """멱등성 캐시 조회"""
        ...

    def get_baseline_owner(self, baseline_id: str) -> str | None:
        """디지털 트윈 베이스라인 소유 테넌트 ID 조회"""
        ...
