"""
Domain Event Object Mapper Implementation

설계 의도:
내부 도메인 이벤트 객체와 컴포넌트 간 전송용 통합 이벤트 DTO(IntegrationEventDto) 간의
상호 변환 및 유효성 검증(trace_id Guard Clause)을 담당합니다.
"""

import logging
from typing import Any

from shared.dtos.integration_event_dto import IntegrationEventDto
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException

logger = logging.getLogger("shared.dtos.domain_event_object_mapper")


class DomainEventObjectMapper:
    """도메인 이벤트 ↔ IntegrationEventDto 변환기"""

    @classmethod
    def to_integration_event(
        cls, domain_event: Any, trace_id: str
    ) -> IntegrationEventDto[Any]:
        """
        도메인 이벤트 객체를 전송용 IntegrationEventDto 패킷으로 변환합니다.

        Newspaper Structure: 고수준 이벤트 매퍼 인터페이스
        """
        cls._validate_trace_id(trace_id)

        event_type = getattr(
            domain_event, "event_type", domain_event.__class__.__name__
        )
        source_component = getattr(domain_event, "source_component", "DomainComponent")
        payload = getattr(domain_event, "payload", domain_event)

        logger.info(
            f"Mapping domain event '{event_type}' to IntegrationEventDto with trace_id: {trace_id}"
        )

        return IntegrationEventDto.create_event(
            event_type=event_type,
            source=source_component,
            payload=payload,
            trace_id=trace_id,
        )

    @classmethod
    def to_domain_event(cls, integration_event: IntegrationEventDto[Any]) -> Any:
        """
        IntegrationEventDto 패킷을 내부 도메인 이벤트/Payload 객체로 역변환합니다.

        Newspaper Structure: 역매핑 인터페이스
        """
        logger.info(
            f"Extracting domain payload from integration event_id: {integration_event.header.get('event_id')}"
        )
        return integration_event.payload

    @classmethod
    def _validate_trace_id(cls, trace_id: str) -> None:
        """
        Guard Clause: trace_id 유효성을 검사하여 누락 또는 빈 문자열 시 예외를 발생시킵니다.

        Newspaper Structure: 세부 검증 로직
        """
        if not trace_id or not isinstance(trace_id, str) or not trace_id.strip():
            logger.error(
                "Validation Error: Invalid or missing trace_id during event mapping."
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
                message="trace_id is required and cannot be empty when mapping domain events.",
                status_code=400,
                details={"provided_trace_id": trace_id},
            )
