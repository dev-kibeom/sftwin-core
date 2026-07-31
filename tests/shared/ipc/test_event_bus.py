"""
Unit Test Specification for EventBus (TC-BUS-01 ~ TC-BUS-03)
"""

from unittest.mock import MagicMock

import pytest

from src.shared.dtos.integration_event_dto import IntegrationEventDto
from src.shared.ipc.event_bus import EventBus


@pytest.fixture
def sample_event():
    return IntegrationEventDto.create_event(
        event_type="TelemetryStreamEvent",
        source="edge_control",
        payload={"sensor_value": 42.5},
        trace_id="TRC-99081234a",
    )


# TC-BUS-01: Happy Path - 등록된 Subscriber로 IntegrationEventDto 전달 검증
def test_tc_bus_01_publish_to_subscribers_success(sample_event):
    mock_system_logger = MagicMock()
    event_bus = EventBus(system_logger=mock_system_logger)

    subscriber_a = MagicMock()
    subscriber_b = MagicMock()

    event_bus.subscribe("telemetry.stream", subscriber_a)
    event_bus.subscribe("telemetry.stream", subscriber_b)

    event_bus.publish("telemetry.stream", sample_event)

    # 핸들러 A와 B가 각각 1회씩 동등하게 호출되었는지 검증
    subscriber_a.assert_called_once_with(sample_event)
    subscriber_b.assert_called_once_with(sample_event)


# TC-BUS-02: Edge Case - 구독자(Subscriber) 부재 토픽 발행 시 Safe Early Return 검증
def test_tc_bus_02_publish_no_subscribers_safe_return(sample_event):
    mock_system_logger = MagicMock()
    event_bus = EventBus(system_logger=mock_system_logger)

    # 아무 구독자도 없는 토픽으로 발행
    event_bus.publish("unknown.topic", sample_event)

    # 예외 없이 Safe Return 되고 debug/info 로그 기록됨을 검증
    mock_system_logger.info.assert_called_once()
    assert (
        "No subscribers for topic 'unknown.topic'"
        in mock_system_logger.info.call_args[0][0]
    )


# TC-BUS-03: Error Handling - Subscriber 핸들러 예외 발생 시 격리(Fault Isolation) 검증
def test_tc_bus_03_subscriber_exception_fault_isolation(sample_event):
    mock_system_logger = MagicMock()
    event_bus = EventBus(system_logger=mock_system_logger)

    # Subscriber A는 런타임 예외 발생하도록 구성
    failing_subscriber = MagicMock(
        side_effect=RuntimeError("Handler A runtime failure!")
    )
    successful_subscriber = MagicMock()

    event_bus.subscribe("telemetry.stream", failing_subscriber)
    event_bus.subscribe("telemetry.stream", successful_subscriber)

    # 실행 시 Subscriber A 예외가 외부로 분출되지 않고 Catch되는지 검증
    try:
        event_bus.publish("telemetry.stream", sample_event)
    except RuntimeError:
        pytest.fail(
            "Fault Isolation failed: RuntimeError was propagated outside EventBus!"
        )

    # Failing Subscriber도 호출 시도가 되었음을 확인
    failing_subscriber.assert_called_once_with(sample_event)

    # GlobalSystemLogger.error가 호출되었음을 검증
    mock_system_logger.error.assert_called_once()

    # call_args에서 positional args 또는 kwargs를 안전하게 추출하여 검증
    call_args, call_kwargs = mock_system_logger.error.call_args
    log_message = call_args[0] if call_args else call_kwargs.get("message", "")
    assert "Fault Isolation Triggered" in log_message

    # Successful Subscriber B는 A의 실패와 상관없이 정상 실행되었는지 검증
    successful_subscriber.assert_called_once_with(sample_event)
