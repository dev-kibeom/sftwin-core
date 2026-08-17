import time
import uuid
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class IntegrationEventDto(Generic[T]):
    """통합 이벤트 메시지 패킷 DTO"""

    header: dict[str, Any]
    payload: T

    @classmethod
    def create_event(
        cls, event_type: str, source: str, payload: T, trace_id: str
    ) -> "IntegrationEventDto[T]":
        """표준 헤더를 자동으로 구성하여 DTO를 생성하는 정적 팩토리 메서드"""

        header = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "source_component": source,
            "timestamp_ns": time.time_ns(),
            "trace_id": trace_id,
        }
        return cls(header=header, payload=payload)
