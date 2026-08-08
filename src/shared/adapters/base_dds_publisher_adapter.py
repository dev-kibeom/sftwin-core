"""
Base DDS Publisher Adapter Implementation

설계 의도:
FastDDS / OPC UA 초저지연 OT 통신 메시지 발행을 추상화하는 기반 클래스입니다.
DDS DomainParticipant 및 Publisher 연결 세션 단절 시 ERR_EDGE_COMM_TIMEOUT 예외를 발송합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes
from src.shared.logging.global_system_logger import GlobalSystemLogger

T = TypeVar("T")


class BaseDdsPublisherAdapter(ABC, Generic[T]):
    """OT 통신 FastDDS/OPC UA Publisher 추상 기반 클래스"""

    def __init__(
        self, participant: Any, publisher: Any, logger: GlobalSystemLogger | None = None
    ):
        self._participant = participant
        self._publisher = publisher
        self._logger = logger or GlobalSystemLogger(
            component_name="BaseDdsPublisherAdapter"
        )

    def publish(self, topic: str, data: T) -> bool:
        """
        Newspaper Structure: OT 메시지 토픽 발행 인터페이스
        """
        # Guard Clause: DDS 연결 세션 유효성 최우선 검사
        if not self._check_connection_status():
            self._logger.error(
                f"DDS Session Invalid: Failed to publish message to topic '{topic}'."
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_EDGE_COMM_TIMEOUT,
                message=f"DDS connection session invalid or timed out while publishing to topic '{topic}'.",
                status_code=504,
                details={"topic": topic},
            )

        self._logger.info(f"Publishing DDS message packet to topic '{topic}'")
        return self._do_publish(topic, data)

    @abstractmethod
    def _do_publish(self, topic: str, data: T) -> bool:
        """
        Newspaper Structure: 하위 Concrete Adapter에서 구현하는 실제 저수준 DDS 발행 연산
        """
        pass

    def _check_connection_status(self) -> bool:
        """
        Newspaper Structure: DDS Participant 세션 상태 검사
        """
        return self._participant is not None and self._publisher is not None
