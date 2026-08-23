import uuid
from dataclasses import dataclass

import pytest
from shared.dtos.global_response_dto import GlobalResponseDto
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.events.domain_event_mapper import DomainEventMapper
from shared.exceptions.base_system_exception import BaseSystemException


@dataclass
class SampleDomainEvent:
    event_type: str = "AssetTwinUpdatedEvent"
    source_component: str = "digital_twin"
    payload: dict | None = None


# TC-DTO-01: Happy Path - 표준 API 성공 응답 Wrapper (GlobalResponseDto) 생성 검증
def test_tc_dto_01_global_response_success():
    data = {"asset_id": "AAS-001"}
    message = "Operation completed successfully."

    response = GlobalResponseDto.success_response(data=data, message=message)

    assert response.success is True, "success flag should be True."
    assert response.code == "SUCCESS", "code should be 'SUCCESS'."
    assert response.message == message
    assert response.data == {"asset_id": "AAS-001"}
    assert response.timestamp is not None, "Timestamp must be generated."


# TC-DTO-02: Happy Path - Domain Event에서 Integration Event 패킷 변환 검증
def test_tc_dto_02_domain_to_integration_event_mapping():
    domain_event = SampleDomainEvent(payload={"status": "ACTIVE"})
    trace_id = "TRC-99081234a"

    integration_event = DomainEventMapper.to_integration_event(domain_event, trace_id)

    assert integration_event.header["trace_id"] == "TRC-99081234a"
    assert integration_event.header["event_type"] == "AssetTwinUpdatedEvent"
    assert integration_event.header["source_component"] == "digital_twin"

    # UUID v4 검증
    event_id = integration_event.header["event_id"]
    parsed_uuid = uuid.UUID(event_id, version=4)
    assert str(parsed_uuid) == event_id, "event_id must be a valid UUID v4."

    assert integration_event.payload == {"status": "ACTIVE"}


# TC-DTO-03: Edge Case - Null Payload 시 표준 에러 응답 Wrapper 생성 검증
def test_tc_dto_03_global_response_error_null_payload():
    code = GlobalErrorCode.ERR_TWIN_NOT_FOUND
    message = "Requested AAS asset does not exist."

    response = GlobalResponseDto.error_response(code=code, message=message, data=None)

    assert response.success is False, "success flag should be False."
    assert response.code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert response.message == message
    assert (
        response.data is None
    ), "data should be None for error response with null payload."


# TC-DTO-04: Error Handling - Trace ID 누락 시 Event DTO 변환 차단 및 예외 검증 (Guard Clause)
def test_tc_dto_04_trace_id_missing_guard_clause():
    domain_event = SampleDomainEvent(payload={"status": "ACTIVE"})

    # trace_id가 빈 문자열인 경우 예외 발생 검증
    with pytest.raises(BaseSystemException) as exc_info:
        DomainEventMapper.to_integration_event(domain_event, trace_id="")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
