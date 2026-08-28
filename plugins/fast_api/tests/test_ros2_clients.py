# File: plugins/fast_api/tests/test_ros2_clients.py
from unittest.mock import MagicMock

import pytest
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode

from plugins.fast_api.adapters.ros2_edge_client import Ros2EdgeServiceClient
from plugins.fast_api.adapters.ros2_webrtc_client import Ros2WebRtcSignalingClient


# ==============================================================================
# Common Mock Fixtures
# ==============================================================================
@pytest.fixture
def create_mock_future():
    """add_done_callback을 즉시 실행해주는 ROS 2 Mock Future 생성 팩토리"""

    def _factory(result_value=None, exception_value=None, is_timeout=False):
        future = MagicMock()
        future.exception.return_value = exception_value
        future.result.return_value = result_value

        def fake_add_done_callback(cb):
            if not is_timeout:
                cb(future)

        future.add_done_callback.side_effect = fake_add_done_callback
        return future

    return _factory


@pytest.fixture
def mock_node():
    node = MagicMock()
    mock_client = MagicMock()
    mock_client.wait_for_service.return_value = True
    node.create_client.return_value = mock_client
    return node


# ==============================================================================
# 1. Ros2EdgeServiceClient Unit Tests
# ==============================================================================
def test_trigger_manual_estop_success(mock_node, create_mock_future):
    # Given
    client = Ros2EdgeServiceClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.error_message = ""

    client._estop_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When
    result = client.call_trigger_estop(
        reason="Collision risk", device_id="EDGE_NODE_001"
    )

    # Then
    assert result is True
    client._estop_client.call_async.assert_called_once()


def test_trigger_manual_estop_failure_raises_failsafe_exception(
    mock_node, create_mock_future
):
    # Given
    client = Ros2EdgeServiceClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.error_message = "Relay trip hardware failure"

    client._estop_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_trigger_estop(reason="Collision risk", device_id="EDGE_NODE_001")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_FAILSAFE_TRIGGERED
    assert exc_info.value.status_code == 503


def test_reset_interlock_success(mock_node, create_mock_future):
    # Given
    client = Ros2EdgeServiceClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = True

    client._reset_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When
    result = client.call_reset_interlock(
        is_field_inspected=True,
        is_manager_approved=True,
        device_id="EDGE_NODE_001",
    )

    # Then
    assert result is True


def test_reset_interlock_denied_raises_conflict_exception(
    mock_node, create_mock_future
):
    # Given: 2단계 안전 승인 실패
    client = Ros2EdgeServiceClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.error_message = "Manager approval is missing."

    client._reset_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_reset_interlock(
            is_field_inspected=True,
            is_manager_approved=False,
            device_id="EDGE_NODE_001",
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_INTERLOCK_RESET_DENIED
    assert exc_info.value.status_code == 409


def test_resume_recovery_success(mock_node, create_mock_future):
    # Given
    client = Ros2EdgeServiceClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.error_message = ""
    mock_response.error_code = ""

    client._resume_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When
    result = client.call_resume_recovery(
        sequence_script="RECOVERY_SEQ_01", device_id="EDGE_NODE_001"
    )

    # Then
    assert result["is_success"] is True
    assert result["error_message"] == ""


def test_resume_recovery_failure_raises_unprocessable_entity(
    mock_node, create_mock_future
):
    # Given
    client = Ros2EdgeServiceClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.error_message = "Recovery script invalid."
    mock_response.error_code = "ERR_RECOVERY_SCRIPT"

    client._resume_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_resume_recovery(
            sequence_script="INVALID_SCRIPT", device_id="EDGE_NODE_001"
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED
    assert exc_info.value.status_code == 422


def test_get_telemetry_success(mock_node, create_mock_future):
    # Given
    client = Ros2EdgeServiceClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.device_id = "EDGE_NODE_001"
    mock_response.timestamp_ns = 1700000000000
    mock_response.joint_positions = [0.1, 0.2, -0.5]
    mock_response.joint_torques = [12.5, 3.2, 0.0]
    mock_response.anomaly_score = 0.02
    mock_response.is_warning = False

    client._telemetry_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When
    telemetry = client.call_get_telemetry(device_id="EDGE_NODE_001")

    # Then
    assert telemetry["device_id"] == "EDGE_NODE_001"
    assert telemetry["anomaly_score"] == 0.02
    assert len(telemetry["joint_positions"]) == 3


def test_edge_service_timeout_raises_gateway_timeout(mock_node, create_mock_future):
    # Given: timeout_sec을 0.01로 짧게 설정하여 타임아웃 유도
    client = Ros2EdgeServiceClient(node=mock_node, timeout_sec=0.01)
    client._estop_client.call_async.return_value = create_mock_future(is_timeout=True)

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_trigger_estop(reason="Timeout test", device_id="EDGE_NODE_001")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT
    assert exc_info.value.status_code == 504


# ==============================================================================
# 2. Ros2WebRtcSignalingClient Unit Tests
# ==============================================================================
def test_webrtc_handle_sdp_offer_success(mock_node, create_mock_future):
    # Given
    client = Ros2WebRtcSignalingClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.sdp_answer = "v=0\r\no=mock_answer..."

    client._sdp_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When
    is_success, sdp_answer = client.call_handle_sdp_offer(
        peer_id="PEER_01", sdp_offer="v=0\r\no=mock_offer..."
    )

    # Then
    assert is_success is True
    assert sdp_answer == "v=0\r\no=mock_answer..."


def test_webrtc_handle_ice_candidate_success(mock_node, create_mock_future):
    # Given
    client = Ros2WebRtcSignalingClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = True

    client._ice_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When
    result = client.call_handle_ice_candidate(
        peer_id="PEER_01", candidate_json='{"candidate":"candidate:1..."}'
    )

    # Then
    assert result is True


def test_webrtc_close_session_success(mock_node, create_mock_future):
    # Given
    client = Ros2WebRtcSignalingClient(node=mock_node)
    mock_response = MagicMock()
    mock_response.is_success = True

    client._close_client.call_async.return_value = create_mock_future(
        result_value=mock_response
    )

    # When
    result = client.call_close_session(peer_id="PEER_01")

    # Then
    assert result is True


def test_webrtc_service_timeout_raises_gateway_timeout(mock_node, create_mock_future):
    # Given: timeout_sec을 0.01로 짧게 설정하여 타임아웃 유도
    client = Ros2WebRtcSignalingClient(node=mock_node, timeout_sec=0.01)
    client._sdp_client.call_async.return_value = create_mock_future(is_timeout=True)

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_handle_sdp_offer(peer_id="PEER_01", sdp_offer="v=0\r\no=...")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT
    assert exc_info.value.status_code == 504
