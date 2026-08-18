from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from shared.context.log_context import LogContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

T = TypeVar("T")


class BaseDdsPublisher(ABC, Generic[T]):
    """FastDDS / OPC UA 초저지연 통신 공통 퍼블리셔 기반 클래스"""

    def __init__(
        self,
        participant: Any,
        publisher: Any,
        component_name: str = "BaseDdsPublisher",
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._participant = participant
        self._publisher = publisher
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name=component_name
        )

    def publish(self, topic: str, data: T, trace_id: str = "TRC-DDS-PUB") -> bool:
        log_ctx = LogContext(
            trace_id=trace_id,
            context={"topic": topic},
        )

        if not self._check_connection_status():
            self._system_logger.error(
                f"DDS Session Invalid: Failed to publish message to topic '{topic}'.",
                log_ctx=log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_EDGE_COMM_TIMEOUT,
                message=f"DDS connection session invalid or timed out while publishing to topic '{topic}'.",
                status_code=504,
                details={"topic": topic},
            )

        self._system_logger.info(
            f"Publishing DDS message packet to topic '{topic}'", log_ctx=log_ctx
        )
        return self._do_publish(topic, data)

    @abstractmethod
    def _do_publish(self, topic: str, data: T) -> bool:
        pass

    def _check_connection_status(self) -> bool:
        return self._participant is not None and self._publisher is not None
