from unittest.mock import MagicMock

import pytest
from shared.dtos.integration_event_dto import IntegrationEventDto
from shared.ipc.event_bus import EventBus


@pytest.fixture
def mock_system_logger():
    return MagicMock()


@pytest.fixture
def event_bus(mock_system_logger):
    return EventBus(system_logger=mock_system_logger)


@pytest.fixture
def sample_event():
    return IntegrationEventDto.create_event(
        event_type="TelemetryStreamEvent",
        source="edge_control",
        payload={"sensor_value": 42.5},
        trace_id="TRC-99081234a",
    )


# TC-BUS-01: Happy Path - 등록된 Subscriber들로 이벤트 정상 브로드캐스트 검증
def test_publish_to_subscribers_success(event_bus, sample_event):
    subscriber_a = MagicMock()
    subscriber_b = MagicMock()

    event_bus.subscribe("telemetry.stream", subscriber_a)
    event_bus.subscribe("telemetry.stream", subscriber_b)

    event_bus.publish("telemetry.stream", sample_event)

    subscriber_a.assert_called_once_with(sample_event)
    subscriber_b.assert_called_once_with(sample_event)


# TC-BUS-02: Edge Case - 구독자 없는 토픽 발행 시 Safe Early Return 검증
def test_publish_no_subscribers_safe_return(
    event_bus, mock_system_logger, sample_event
):
    event_bus.publish("unknown.topic", sample_event)

    # 핸들러가 없으므로 debug 로그 기록 및 안전 종료 검증
    mock_system_logger.debug.assert_called_once()


# TC-BUS-03: Error Handling - Subscriber 예외 발생 시 Fault Isolation 격리 검증
def test_subscriber_exception_fault_isolation(
    event_bus, mock_system_logger, sample_event
):
    failing_subscriber = MagicMock(side_effect=RuntimeError("Handler A failure"))
    successful_subscriber = MagicMock()

    event_bus.subscribe("telemetry.stream", failing_subscriber)
    event_bus.subscribe("telemetry.stream", successful_subscriber)

    # 예외 전파 없이 안전하게 격리되어 실행되는지 검증
    event_bus.publish("telemetry.stream", sample_event)

    failing_subscriber.assert_called_once_with(sample_event)
    successful_subscriber.assert_called_once_with(sample_event)
    mock_system_logger.error.assert_called_once()

    call_args, call_kwargs = mock_system_logger.error.call_args
    log_message = call_args[0] if call_args else call_kwargs.get("message", "")
    assert "Fault Isolation Triggered" in log_message
