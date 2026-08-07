"""
@file redis_cache_adapter.py
@description 멱등성 보장 및 캐싱을 위한 Redis 통신 어댑터
"""

import json
import logging
import os
from typing import Any

import redis

logger = logging.getLogger("shared.adapters.redis_cache_adapter")


class RedisCacheAdapter:
    def __init__(self, redis_client: Any = None):
        if redis_client:
            self._redis_client = redis_client
        else:
            redis_host = os.getenv("REDIS_HOST", "sftwin-redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            try:
                self._redis_client = redis.Redis(
                    host=redis_host, port=redis_port, db=0, socket_timeout=2
                )
            except Exception as e:
                logger.warning(
                    f"Redis Client connection failed: {e}. Fallback to in-memory dict."
                )
                self._redis_client = None

        self._local_fallback: dict[str, Any] = {}

    def get_cached_quote(self, idempotency_key: str) -> dict[str, Any] | None:
        if self._redis_client:
            try:
                data = self._redis_client.get(f"quote:{idempotency_key}")
                if data:
                    return json.loads(data)
                return None
            except Exception as e:
                logger.warning(f"Redis GET failed: {e}")

        return self._local_fallback.get(idempotency_key)

    def set_cached_quote(
        self, idempotency_key: str, data: dict[str, Any], ttl: int = 86400
    ) -> bool:
        if self._redis_client:
            try:
                self._redis_client.setex(
                    f"quote:{idempotency_key}", ttl, json.dumps(data)
                )
                return True
            except Exception as e:
                logger.warning(f"Redis SETEX failed: {e}")

        self._local_fallback[idempotency_key] = data
        return True
