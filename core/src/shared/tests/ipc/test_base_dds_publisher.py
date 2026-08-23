from unittest.mock import MagicMock

import pytest
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.ipc.base_dds_publisher import BaseDdsPublisher


class ConcreteDdsPublisher(BaseDdsPublisher[dict]):
    """추상 메서드 _do_publish 구현용 테스트 더블"""

    def _do_publish(self, topic: str, data: dict) -> bool:
        return self._publisher.write_data(topic, data)


@pytest.fixture
def mock_dds_session():
    """정상 연결된 Participant 및 Publisher Mock 생성"""
    mock_participant = MagicMock()
    mock_publisher = MagicMock()
    mock_publisher.write_data.return_value = True
    return mock_participant, mock_publisher


@pytest.fixture
def dds_publisher(mock_dds_session):
    """정상 연결 상태의 BaseDdsPublisher 인스턴스 Fixture"""
    participant, publisher = mock_dds_session
    return ConcreteDdsPublisher(participant=participant, publisher=publisher)


# TC-DDS-01: Happy Path - FastDDS Topic 메시지 정상 Publish 검증
def test_publish_success(dds_publisher, mock_dds_session):
    _, mock_publisher = mock_dds_session
    topic = "factory/telemetry"
    payload = {"speed": 100, "status": "RUNNING"}

    success = dds_publisher.publish(topic=topic, data=payload, trace_id="TRC-TEST-001")

    assert success is True
    mock_publisher.write_data.assert_called_once_with(topic, payload)


# TC-DDS-02: Edge Case - DDS 세션 단절/무효 시 ERR_EDGE_COMM_TIMEOUT 예외 변환 검증
def test_publish_session_disconnected_raises_exception():
    disconnected_publisher = ConcreteDdsPublisher(participant=None, publisher=None)

    with pytest.raises(BaseSystemException) as exc_info:
        disconnected_publisher.publish(
            topic="factory/telemetry",
            data={"speed": 100},
            trace_id="TRC-DISCONNECTED",
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT
    assert exc_info.value.status_code == 504
