import asyncio
import inspect
from collections.abc import Callable
from threading import RLock
from typing import Any

from shared.context.log_context import LogContext
from shared.dtos.integration_event_dto import IntegrationEventDto
from shared.logger.global_system_logger import GlobalSystemLogger


class EventBus:
    """스레드 안전 및 동기/비동기 디스패치를 지원하는 인프로세스 이벤트 버스"""

    def __init__(self, system_logger: GlobalSystemLogger | None = None) -> None:
        self._subscribers: dict[
            str, list[Callable[[IntegrationEventDto[Any]], Any]]
        ] = {}
        self._lock = RLock()
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="EventBusComponent"
        )

    def subscribe(
        self, topic: str, handler: Callable[[IntegrationEventDto[Any]], Any]
    ) -> None:
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            if handler not in self._subscribers[topic]:
                self._subscribers[topic].append(handler)

        log_ctx = LogContext(
            context={
                "topic": topic,
                "handler": getattr(handler, "__name__", str(handler)),
            }
        )
        self._system_logger.debug(
            f"Registered subscriber handler for topic '{topic}'", log_ctx=log_ctx
        )

    def unsubscribe(
        self, topic: str, handler: Callable[[IntegrationEventDto[Any]], Any]
    ) -> None:
        with self._lock:
            if topic in self._subscribers and handler in self._subscribers[topic]:
                self._subscribers[topic].remove(handler)

    def publish(self, topic: str, event: IntegrationEventDto[Any]) -> None:
        with self._lock:
            handlers = list(self._subscribers.get(topic, []))

        trace_id = self._extract_trace_id(event)
        event_id = self._extract_event_id(event)

        log_ctx = LogContext(
            trace_id=trace_id,
            context={
                "topic": topic,
                "event_id": event_id,
                "subscriber_count": len(handlers),
            },
        )

        if not handlers:
            self._system_logger.debug(
                f"No subscribers registered for topic '{topic}'. Safe early return executed.",
                log_ctx=log_ctx,
            )
            return

        self._system_logger.info(
            f"Publishing IntegrationEventDto to {len(handlers)} subscriber(s) on topic '{topic}'",
            log_ctx=log_ctx,
        )

        for handler in handlers:
            self._safe_dispatch(handler, event, topic, trace_id, event_id)

    def _safe_dispatch(
        self,
        handler: Callable[[IntegrationEventDto[Any]], Any],
        event: IntegrationEventDto[Any],
        topic: str,
        trace_id: str,
        event_id: str,
    ) -> None:
        try:
            if inspect.iscoroutinefunction(handler):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(handler(event))
                except RuntimeError:
                    asyncio.run(handler(event))
            else:
                handler(event)
        except Exception as exc:
            handler_name = getattr(handler, "__name__", str(handler))
            log_ctx = LogContext(
                trace_id=trace_id,
                context={
                    "topic": topic,
                    "event_id": event_id,
                    "handler_name": handler_name,
                    "exception_class": exc.__class__.__name__,
                },
                exc=exc,
            )
            self._system_logger.error(
                f"Fault Isolation Triggered: Subscriber '{handler_name}' raised exception: {str(exc)}",
                log_ctx=log_ctx,
            )

    def _extract_trace_id(self, event: IntegrationEventDto[Any]) -> str:
        if isinstance(event, IntegrationEventDto) and hasattr(event, "header"):
            return str(event.header.get("trace_id", "TRC-EVENTBUS"))
        return "TRC-EVENTBUS"

    def _extract_event_id(self, event: IntegrationEventDto[Any]) -> str:
        if isinstance(event, IntegrationEventDto) and hasattr(event, "header"):
            return str(event.header.get("event_id", "UNKNOWN"))
        return "UNKNOWN"
