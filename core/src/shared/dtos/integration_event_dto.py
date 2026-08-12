"""
Integration Event DTO Specification

설계 의도:
Event Bus 및 POSIX Shared Memory IPC 전송 시 사용되는 표준 비동기 이벤트 패킷 규격입니다.
UUID v4 기반 event_id, timestamp_ns, trace_id를 보유하는 표준 헤더와 Payload를 결합합니다.
"""

import time
import uuid
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class IntegrationEventDto(Generic[T]):
    """통합 이벤트 메시지 패킷 DTO"""

    header: dict[str, Any]
    payload: T

    @classmethod
    def create_event(
        cls, event_type: str, source: str, payload: T, trace_id: str
    ) -> "IntegrationEventDto[T]":
        """
        표준 헤더를 자동으로 구성하여 IntegrationEventDto 객체를 생성하는 정적 팩토리 메서드

        Newspaper Structure: 팩토리 메서드 구현
        """
        header = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "source_component": source,
            "timestamp_ns": time.time_ns(),
            "trace_id": trace_id,
        }
        return cls(header=header, payload=payload)
