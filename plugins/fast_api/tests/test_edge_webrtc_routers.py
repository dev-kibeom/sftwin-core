# File: plugins/fast_api/tests/test_edge_webrtc_routers.py

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from polyfactory.factories.pydantic_factory import ModelFactory
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole

from plugins.fast_api.adapters.ros2_edge_client import Ros2EdgeServiceClient
from plugins.fast_api.adapters.ros2_webrtc_client import Ros2WebRtcSignalingClient
from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.clients import (
    get_ros2_edge_service_client,
    get_ros2_webrtc_signaling_client,
)
from plugins.fast_api.middlewares.exception_handler import (
    register_exception_handlers,
)
from plugins.fast_api.routers.edge_router import router as edge_router
from plugins.fast_api.routers.webrtc_router import router as webrtc_router
from plugins.fast_api.schemas.requests import (
    ResetInterlockRequestSchema,
    ResumeRecoveryRequestSchema,
    TriggerManualEstopRequestSchema,
    WebRtcIceCandidateRequestSchema,
    WebRtcSdpOfferRequestSchema,
)


# --- Polyfactory Schema Factories ---
class ManualEstopRequestSchemaFactory(ModelFactory[TriggerManualEstopRequestSchema]):
    __model__ = TriggerManualEstopRequestSchema


class ResetInterlockRequestSchemaFactory(ModelFactory[ResetInterlockRequestSchema]):
    __model__ = ResetInterlockRequestSchema


class ResumeRecoveryRequestSchemaFactory(ModelFactory[ResumeRecoveryRequestSchema]):
    __model__ = ResumeRecoveryRequestSchema


class WebRtcSdpOfferRequestSchemaFactory(ModelFactory[WebRtcSdpOfferRequestSchema]):
    __model__ = WebRtcSdpOfferRequestSchema


class WebRtcIceCandidateRequestSchemaFactory(
    ModelFactory[WebRtcIceCandidateRequestSchema]
):
    __model__ = WebRtcIceCandidateRequestSchema


# --- Test Fixtures ---
@pytest.fixture
def mock_edge_client():
    return MagicMock(spec=Ros2EdgeServiceClient)


@pytest.fixture
def mock_webrtc_client():
    return MagicMock(spec=Ros2WebRtcSignalingClient)


@pytest.fixture
def mock_user_context():
    return UserContext(
        user_id="USR-999",
        username="edge_admin",
        company_id="COMP-A",
        role=UserRole.FACTORY_MANAGER,
        accessible_factory_ids=["FAC-01"],
        is_edge_authenticated=True,
    )


@pytest.fixture
def app(
    mock_edge_client,
    mock_webrtc_client,
    mock_user_context,
) -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    test_app.include_router(edge_router, prefix="/api/v1")
    test_app.include_router(webrtc_router, prefix="/api/v1")

    test_app.dependency_overrides[get_current_user_context] = lambda: mock_user_context
    test_app.dependency_overrides[get_ros2_edge_service_client] = lambda: (
        mock_edge_client
    )
    test_app.dependency_overrides[get_ros2_webrtc_signaling_client] = lambda: (
        mock_webrtc_client
    )

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ==============================================================================
# 1. Edge Router Tests
# ==============================================================================
def test_trigger_manual_estop_success(
    client: TestClient,
    mock_edge_client: MagicMock,
):
    # Given
    mock_edge_client.call_trigger_estop.return_value = True
    payload = {
        "reason": "Human detected in robot working cell",
        "device_id": "ROBOT-01",
    }

    # When
    response = client.post("/api/v1/edge/estop", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] is True

    mock_edge_client.call_trigger_estop.assert_called_once_with(
        reason="Human detected in robot working cell",
        device_id="ROBOT-01",
    )


def test_trigger_manual_estop_hardware_failure_returns_503(
    client: TestClient,
    mock_edge_client: MagicMock,
):
    # Given
    mock_edge_client.call_trigger_estop.side_effect = BaseSystemException(
        error_code=GlobalErrorCode.ERR_EDGE_FAILSAFE_TRIGGERED,
        message="Relay hardware circuit trip failed.",
        status_code=503,
    )
    payload = {"reason": "Overheat", "device_id": "ROBOT-01"}

    # When
    response = client.post("/api/v1/edge/estop", json=payload)

    # Then
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_EDGE_FAILSAFE_TRIGGERED


def test_reset_interlock_success(
    client: TestClient,
    mock_edge_client: MagicMock,
):
    # Given
    mock_edge_client.call_reset_interlock.return_value = True
    payload = {
        "is_field_inspected": True,
        "is_manager_approved": True,
        "device_id": "ROBOT-01",
    }

    # When
    response = client.post("/api/v1/edge/reset-interlock", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] is True

    mock_edge_client.call_reset_interlock.assert_called_once_with(
        is_field_inspected=True,
        is_manager_approved=True,
        device_id="ROBOT-01",
    )


def test_reset_interlock_denied_returns_409(
    client: TestClient,
    mock_edge_client: MagicMock,
):
    # Given
    mock_edge_client.call_reset_interlock.side_effect = BaseSystemException(
        error_code=GlobalErrorCode.ERR_EDGE_INTERLOCK_RESET_DENIED,
        message="Manager approval missing for 2-step verification.",
        status_code=409,
    )
    payload = {
        "is_field_inspected": True,
        "is_manager_approved": False,
        "device_id": "ROBOT-01",
    }

    # When
    response = client.post("/api/v1/edge/reset-interlock", json=payload)

    # Then
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_EDGE_INTERLOCK_RESET_DENIED


def test_resume_recovery_success(
    client: TestClient,
    mock_edge_client: MagicMock,
):
    # Given
    mock_edge_client.call_resume_recovery.return_value = {
        "is_success": True,
        "error_message": "",
        "error_code": "",
    }
    payload = {
        "sequence_script": "ROBOT.HOMING(); ROBOT.START();",
        "device_id": "ROBOT-01",
    }

    # When
    response = client.post("/api/v1/edge/resume-recovery", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["is_success"] is True

    mock_edge_client.call_resume_recovery.assert_called_once_with(
        sequence_script="ROBOT.HOMING(); ROBOT.START();",
        device_id="ROBOT-01",
    )


def test_get_telemetry_success(
    client: TestClient,
    mock_edge_client: MagicMock,
):
    # Given
    mock_edge_client.call_get_telemetry.return_value = {
        "device_id": "ROBOT-01",
        "timestamp_ns": 1718000000000,
        "joint_positions": [0.0, 1.57, -1.57, 0.0, 0.0, 0.0],
        "joint_torques": [10.2, 5.5, 3.1, 0.0, 0.0, 0.0],
        "anomaly_score": 0.02,
        "is_warning": False,
    }

    # When
    response = client.get("/api/v1/edge/telemetry/ROBOT-01")

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["device_id"] == "ROBOT-01"
    assert body["data"]["is_warning"] is False

    mock_edge_client.call_get_telemetry.assert_called_once_with(device_id="ROBOT-01")


# ==============================================================================
# 2. WebRTC Router Tests
# ==============================================================================
def test_webrtc_handle_sdp_offer_success(
    client: TestClient,
    mock_webrtc_client: MagicMock,
):
    # Given
    mock_webrtc_client.call_handle_sdp_offer.return_value = (
        True,
        "v=0\r\no=mock_answer_sdp...",
    )
    payload = {
        "peer_id": "CLIENT-001",
        "sdp_offer": "v=0\r\no=mock_offer_sdp...",
    }

    # When
    response = client.post("/api/v1/webrtc/offer", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["peer_id"] == "CLIENT-001"
    assert body["data"]["sdp_answer"] == "v=0\r\no=mock_answer_sdp..."

    mock_webrtc_client.call_handle_sdp_offer.assert_called_once_with(
        peer_id="CLIENT-001",
        sdp_offer="v=0\r\no=mock_offer_sdp...",
    )


def test_webrtc_handle_ice_candidate_success(
    client: TestClient,
    mock_webrtc_client: MagicMock,
):
    # Given
    mock_webrtc_client.call_handle_ice_candidate.return_value = True
    payload = {
        "peer_id": "CLIENT-001",
        "candidate_json": '{"candidate":"candidate:1 1 UDP ..."}',
    }

    # When
    response = client.post("/api/v1/webrtc/ice-candidate", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] is True

    mock_webrtc_client.call_handle_ice_candidate.assert_called_once_with(
        peer_id="CLIENT-001",
        candidate_json='{"candidate":"candidate:1 1 UDP ..."}',
    )


def test_webrtc_close_session_success(
    client: TestClient,
    mock_webrtc_client: MagicMock,
):
    # Given
    mock_webrtc_client.call_close_session.return_value = True
    payload = {"peer_id": "CLIENT-001"}

    # When
    response = client.post("/api/v1/webrtc/sessions/CLIENT-001/close", json=payload)
    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] is True

    mock_webrtc_client.call_close_session.assert_called_once_with(peer_id="CLIENT-001")
