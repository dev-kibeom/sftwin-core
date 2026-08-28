# File: plugins/fast_api/tests/test_ros2_clients.py

from unittest.mock import MagicMock
import pytest

from plugins.fast_api.adapters.ros2_edge_client import Ros2EdgeServiceClient
from plugins.fast_api.adapters.ros2_webrtc_client import Ros2WebRtcSignalingClient
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode


# ==============================================================================
# 1. Ros2EdgeServiceClient Unit Tests
# ==============================================================================
@pytest.fixture
def mock_edge_node():
    node = MagicMock()
    # Mock clients created in constructor
    mock_client = MagicMock()
    mock_client.wait_for_service.return_value = True
    node.create_client.return_value = mock_client
    return node


def test_trigger_manual_estop_success(mock_edge_node):
    # Given
    client = Ros2EdgeServiceClient(node=mock_edge_node)
    mock_future = MagicMock()
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.error_message = ""
    mock_future.result.return_value = mock_response

    client._estop_client.call_async.return_value = mock_future
    mock_edge_node.executor.spin_until_future_complete.return_value = None

    # When
    result = client.call_trigger_estop(
        reason="Collision risk", device_id="EDGE_NODE_001"
    )

    # Then
    assert result is True
    client._estop_client.call_async.assert_called_once()


def test_trigger_manual_estop_failure_raises_failsafe_exception(mock_edge_node):
    # Given
    client = Ros2EdgeServiceClient(node=mock_edge_node)
    mock_future = MagicMock()
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.error_message = "Relay trip hardware failure"
    mock_future.result.return_value = mock_response

    client._estop_client.call_async.return_value = mock_future

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_trigger_estop(reason="Collision risk", device_id="EDGE_NODE_001")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_FAILSAFE_TRIGGERED
    assert exc_info.value.status_code == 503


def test_reset_interlock_success(mock_edge_node):
    # Given
    client = Ros2EdgeServiceClient(node=mock_edge_node)
    mock_future = MagicMock()
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_future.result.return_value = mock_response

    client._reset_client.call_async.return_value = mock_future

    # When
    result = client.call_reset_interlock(
        is_field_inspected=True,
        is_manager_approved=True,
        device_id="EDGE_NODE_001",
    )

    # Then
    assert result is True


def test_reset_interlock_denied_raises_conflict_exception(mock_edge_node):
    # Given: 2-step verification failed on edge
    client = Ros2EdgeServiceClient(node=mock_edge_node)
    mock_future = MagicMock()
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.error_message = "Manager approval is missing."
    mock_future.result.return_value = mock_response

    client._reset_client.call_async.return_value = mock_future

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_reset_interlock(
            is_field_inspected=True,
            is_manager_approved=False,
            device_id="EDGE_NODE_001",
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_INTERLOCK_RESET_DENIED
    assert exc_info.value.status_code == 409


def test_resume_recovery_failure_raises_unprocessable_entity(mock_edge_node):
    # Given
    client = Ros2EdgeServiceClient(node=mock_edge_node)
    mock_future = MagicMock()
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.error_message = "Recovery script invalid."
    mock_response.error_code = "ERR_RECOVERY_SCRIPT"
    mock_future.result.return_value = mock_response

    client._resume_client.call_async.return_value = mock_future

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_resume_recovery(
            sequence_script="INVALID_SCRIPT", device_id="EDGE_NODE_001"
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED
    assert exc_info.value.status_code == 422


# ==============================================================================
# 2. Ros2WebRtcSignalingClient Unit Tests
# ==============================================================================
@pytest.fixture
def mock_webrtc_node():
    node = MagicMock()
    mock_client = MagicMock()
    mock_client.wait_for_service.return_value = True
    node.create_client.return_value = mock_client
    return node


def test_webrtc_handle_sdp_offer_success(mock_webrtc_node):
    # Given
    client = Ros2WebRtcSignalingClient(node=mock_webrtc_node)
    mock_future = MagicMock()
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.sdp_answer = "v=0\r\no=mock_answer..."
    mock_future.result.return_value = mock_response

    client._sdp_client.call_async.return_value = mock_future

    # When
    is_success, sdp_answer = client.call_handle_sdp_offer(
        peer_id="PEER_01", sdp_offer="v=0\r\no=mock_offer..."
    )

    # Then
    assert is_success is True
    assert sdp_answer == "v=0\r\no=mock_answer..."


def test_webrtc_handle_ice_candidate_success(mock_webrtc_node):
    # Given
    client = Ros2WebRtcSignalingClient(node=mock_webrtc_node)
    mock_future = MagicMock()
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_future.result.return_value = mock_response

    client._ice_client.call_async.return_value = mock_future

    # When
    result = client.call_handle_ice_candidate(
        peer_id="PEER_01", candidate_json='{"candidate":"candidate:1..."}'
    )

    # Then
    assert result is True


def test_webrtc_service_timeout_raises_gateway_timeout(mock_webrtc_node):
    # Given
    client = Ros2WebRtcSignalingClient(node=mock_webrtc_node)
    # Service call timeout simulation (future.result() returns None or timeout)
    client._sdp_client.call_async.side_effect = TimeoutError(
        "ROS2 service call timeout"
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        client.call_handle_sdp_offer(peer_id="PEER_01", sdp_offer="v=0\r\no=...")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT
    assert exc_info.value.status_code == 504
