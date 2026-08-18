from typing import Any, Protocol


class IQuoteIdempotencyStore(Protocol):
    """중복 요청 방지 및 응답 캐싱 전용 포트"""

    def find_cached_quote(self, idempotency_key: str) -> dict[str, Any] | None:
        """캐시된 견적 결과 조회"""
        ...

    def save_cached_quote(
        self, idempotency_key: str, data: dict[str, Any], ttl_seconds: int = 86400
    ) -> None:
        """견적 결과 멱등성 캐시 저장"""
        ...
