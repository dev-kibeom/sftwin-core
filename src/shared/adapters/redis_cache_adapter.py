"""
@file redis_cache_adapter.py
@description 멱등성 보장 및 캐싱을 위한 Redis 통신 어댑터
"""

from typing import Any


class RedisCacheAdapter:
    def __init__(self, redis_client: Any = None):
        self._redis_client = redis_client
        self._local_fallback = {}  # Redis 미연결 시 메모리 Fallback용 Stub

    def get_cached_quote(self, idempotency_key: str) -> dict[str, Any] | None:
        return self._local_fallback.get(idempotency_key)

    def set_cached_quote(
        self, idempotency_key: str, data: dict[str, Any], ttl: int
    ) -> bool:
        self._local_fallback[idempotency_key] = data
        return True
