"""
Unit Test Specification for BaseDdsPublisherAdapter (TC-ADP-02, Edge Case)
"""

from unittest.mock import MagicMock

import pytest
from shared.adapters.base_dds_publisher_adapter import BaseDdsPublisherAdapter
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException


class ConcreteFastDdsPublisherAdapter(BaseDdsPublisherAdapter[dict]):
    """테스트용 Concrete FastDDS Publisher Adapter"""

    def _do_publish(self, topic: str, data: dict) -> bool:
        return self._publisher.write_data(topic, data)


# TC-ADP-02: Happy Path - FastDDS Topic 메시지 정상 Publish 검증
def test_tc_adp_02__failsafe_publish_success():
    mock_participant = MagicMock()
    mock_publisher = MagicMock()
    mock_publisher.write_data.return_value = True

    adapter = ConcreteFastDdsPublisherAdapter(
        participant=mock_participant, publisher=mock_publisher
    )
    success = adapter.publish(topic="telemetry", data={"speed": 100})

    assert success is True
    mock_publisher.write_data.assert_called_once_with("telemetry", {"speed": 100})


# Edge Case: DDS Session 무효 상태 시 ERR_EDGE_COMM_TIMEOUT 예외 발송 검증
def test_tc_adp_02_edge_dds_session_disconnected():
    adapter = ConcreteFastDdsPublisherAdapter(participant=None, publisher=None)

    with pytest.raises(BaseSystemException) as exc_info:
        adapter.publish(topic="telemetry", data={"speed": 100})

    assert exc_info.value.error_code == GlobalErrorCodeEnum.ERR_EDGE_COMM_TIMEOUT
    assert exc_info.value.status_code == 504
