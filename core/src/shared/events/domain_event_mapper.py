from typing import Any

from shared.context.log_context import LogContext
from shared.dtos.integration_event_dto import IntegrationEventDto
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

_system_logger = GlobalSystemLogger(component_name="DomainEventMapper")


class DomainEventMapper:
    """도메인 이벤트 ↔ IntegrationEventDto 변환기"""

    @classmethod
    def to_integration_event(
        cls, domain_event: Any, trace_id: str
    ) -> IntegrationEventDto[Any]:
        cls._validate_trace_id(trace_id)

        event_type = getattr(
            domain_event, "event_type", domain_event.__class__.__name__
        )
        source_component = getattr(domain_event, "source_component", "DomainComponent")
        payload = getattr(domain_event, "payload", domain_event)

        log_ctx = LogContext(
            trace_id=trace_id,
            context={"event_type": event_type, "source": source_component},
        )
        _system_logger.debug(
            f"Mapping domain event '{event_type}' to IntegrationEventDto",
            log_ctx=log_ctx,
        )

        return IntegrationEventDto.create_event(
            event_type=event_type,
            source=source_component,
            payload=payload,
            trace_id=trace_id,
        )

    @classmethod
    def to_domain_event(cls, integration_event: IntegrationEventDto[Any]) -> Any:
        event_id = integration_event.header.get("event_id", "UNKNOWN")
        trace_id = integration_event.header.get("trace_id", "TRC-DEFAULT")

        log_ctx = LogContext(
            trace_id=trace_id,
            context={"event_id": event_id},
        )
        _system_logger.debug(
            f"Extracting domain payload from integration event_id: {event_id}",
            log_ctx=log_ctx,
        )

        return integration_event.payload

    @classmethod
    def _validate_trace_id(cls, trace_id: str) -> None:
        if not trace_id or not isinstance(trace_id, str) or not trace_id.strip():
            log_ctx = LogContext(
                trace_id="TRC-INVALID",
                context={"provided_trace_id": trace_id},
            )
            _system_logger.error(
                "Validation Error: Invalid or missing trace_id during event mapping.",
                log_ctx=log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
                message="trace_id is required and cannot be empty when mapping domain events.",
                status_code=400,
                details={"provided_trace_id": trace_id},
            )
