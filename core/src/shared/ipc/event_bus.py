"""
Global Event Bus & IPC Implementation

설계 의도:
단일 프로세스 내 각 컴포넌트 간 비동기 이벤트 중계(Pub/Sub)를 담당하는 이벤트 버스 클래스입니다.
특정 도메인 엔티티에 직접 의존하지 않고 IntegrationEventDto 패킷만을 전달하며,
단일 Subscriber의 런타임 예외가 다른 Subscriber의 실행을 방해하지 않도록 완벽히 격리(Fault Isolation)합니다.
"""

import logging
from collections.abc import Callable
from typing import Any

from src.shared.dtos.integration_event_dto import IntegrationEventDto
from src.shared.dtos.log_dtos import LogContext
from src.shared.logger.global_system_logger import GlobalSystemLogger

logger = logging.getLogger("shared.ipc.event_bus")


class EventBus:
    """프로세스 내 비동기 Pub/Sub 메모리 이벤트 버스"""

    def __init__(self, system_logger: Any = None):
        self._subscribers: dict[str, list[Callable[[IntegrationEventDto], None]]] = {}
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="EventBusComponent"
        )

    def subscribe(
        self, topic: str, handler: Callable[[IntegrationEventDto], None]
    ) -> None:
        """
        Newspaper Structure: 특정 토픽에 대한 이벤트 구독 콜백 핸들러 등록 인터페이스
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []

        self._subscribers[topic].append(handler)
        logger.info(f"Registered subscriber handler for topic '{topic}'")

    def publish(self, topic: str, event: IntegrationEventDto) -> None:
        """
        Newspaper Structure: 지정된 토픽으로 IntegrationEventDto 패킷 중계 및 방출
        """
        handlers = self._subscribers.get(topic, [])

        # Guard 1: 등록된 Subscriber 부재 시 Safe Early Return
        if not handlers:
            logger.debug(
                f"No subscribers registered for topic '{topic}'. Safe early return executed."
            )
            self._system_logger.info(
                f"EventBus debug: No subscribers for topic '{topic}'"
            )
            return

        logger.info(
            f"Publishing IntegrationEventDto to {len(handlers)} subscriber(s) on topic '{topic}'"
        )

        # 각 구독자 핸들러로 예외 격리(Fault Isolation) 디스패치 수행
        for handler in handlers:
            self._safe_dispatch(handler, event)

    def _safe_dispatch(
        self, handler: Callable[[IntegrationEventDto], None], event: IntegrationEventDto
    ) -> None:
        """
        Fault Isolation Guard Pattern:
        단일 핸들러의 실행 실패가 다른 핸들러나 전체 EventBus 흐름으로 전파되지 않도록 개별 try-except로 격리합니다.

        Newspaper Structure: 세부 예외 포획 및 디스패치 보호 메서드
        """
        try:
            handler(event)
        except Exception as exc:
            event_id = (
                event.header.get("event_id")
                if isinstance(event, IntegrationEventDto) and hasattr(event, "header")
                else "UNKNOWN"
            )
            raw_trace_id = (
                event.header.get("trace_id")
                if isinstance(event, IntegrationEventDto) and hasattr(event, "header")
                else None
            )
            trace_id: str = str(raw_trace_id) if raw_trace_id else "TRC-UNKNOWN"

            handler_name = getattr(handler, "__name__", str(handler))

            logger.error(
                f"Fault Isolation: Subscriber handler '{handler_name}' failed for topic event_id [{event_id}]: {str(exc)}",
                exc_info=True,
            )

            # LogContext에 trace_id 및 컨텍스트 정보를 포함하여 전파
            log_ctx = LogContext(
                trace_id=trace_id,
                context={
                    "event_id": event_id,
                    "handler_name": handler_name,
                    "exception_class": exc.__class__.__name__,
                },
                exc=exc,
            )
            self._system_logger.error(
                message=f"Fault Isolation Triggered: Subscriber '{handler_name}' raised exception: {str(exc)}",
                log_ctx=log_ctx,
            )
