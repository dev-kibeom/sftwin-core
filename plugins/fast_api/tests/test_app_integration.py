# File: plugins/fast_api/tests/test_app_integration.py
from unittest.mock import MagicMock, patch

import pytest
from digital_twin.contracts.dtos.asset_dto import AssetDto
from fastapi import FastAPI
from fastapi.testclient import TestClient
from polyfactory.factories.dataclass_factory import DataclassFactory
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole

from plugins.fast_api.adapters.ros2_edge_client import Ros2EdgeServiceClient
from plugins.fast_api.adapters.ros2_webrtc_client import Ros2WebRtcSignalingClient
from plugins.fast_api.app import create_app
from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.clients import (
    get_ros2_edge_service_client,
    get_ros2_webrtc_signaling_client,
)
from plugins.fast_api.dependencies.facades import (
    get_digital_twin_command_facade,
    get_digital_twin_query_facade,
    get_simulation_command_facade,
    get_simulation_query_facade,
)


# --- Polyfactory Factories ---
class AssetDtoFactory(DataclassFactory[AssetDto]):
    __model__ = AssetDto


# --- Test Fixtures ---
@pytest.fixture
def mock_user_context():
    return UserContext(
        user_id="USR-INTEG-01",
        username="integration_tester",
        company_id="COMP-A",
        role=UserRole.FACTORY_MANAGER,
        accessible_factory_ids=["FAC-01"],
        is_edge_authenticated=True,
    )


@pytest.fixture
def mock_dt_command_facade():
    return MagicMock()


@pytest.fixture
def mock_dt_query_facade():
    return MagicMock()


@pytest.fixture
def mock_sim_command_facade():
    return MagicMock()


@pytest.fixture
def mock_sim_query_facade():
    return MagicMock()


@pytest.fixture
def mock_edge_client():
    return MagicMock(spec=Ros2EdgeServiceClient)


@pytest.fixture
def mock_webrtc_client():
    return MagicMock(spec=Ros2WebRtcSignalingClient)


@pytest.fixture
def app(
    mock_user_context,
    mock_dt_command_facade,
    mock_dt_query_facade,
    mock_sim_command_facade,
    mock_sim_query_facade,
    mock_edge_client,
    mock_webrtc_client,
    monkeypatch,
):
    # 테스트 환경 플래그 설정
    monkeypatch.setenv("TESTING", "1")

    application = create_app()

    # Core/Adapter DI Overrides
    application.dependency_overrides[get_current_user_context] = lambda: (
        mock_user_context
    )
    application.dependency_overrides[get_digital_twin_command_facade] = lambda: (
        mock_dt_command_facade
    )
    application.dependency_overrides[get_digital_twin_query_facade] = lambda: (
        mock_dt_query_facade
    )
    application.dependency_overrides[get_simulation_command_facade] = lambda: (
        mock_sim_command_facade
    )
    application.dependency_overrides[get_simulation_query_facade] = lambda: (
        mock_sim_query_facade
    )
    application.dependency_overrides[get_ros2_edge_service_client] = lambda: (
        mock_edge_client
    )
    application.dependency_overrides[get_ros2_webrtc_signaling_client] = lambda: (
        mock_webrtc_client
    )

    return application


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


# ==============================================================================
# 1. Composition Root & Health Check Tests
# ==============================================================================
def test_health_check_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "version" in body


def test_openapi_json_accessible_with_correct_tags(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/assets" in schema["paths"]
    assert "/api/v1/twins/baselines/{baseline_id}/layout" in schema["paths"]
    assert "/api/v1/simulations/run" in schema["paths"]
    assert "/api/v1/edge/estop" in schema["paths"]
    assert "/api/v1/webrtc/offer" in schema["paths"]


# ==============================================================================
# 2. Middleware & Correlation ID End-to-End Propagation Tests
# ==============================================================================
def test_correlation_id_propagates_through_router_response(
    client: TestClient,
    mock_dt_query_facade: MagicMock,
    mock_user_context: UserContext,
):
    mock_asset = AssetDtoFactory.build(
        asset_id="ASSET-777",
        company_id="COMP-A",
    )
    mock_dt_query_facade.get_asset.return_value = mock_asset
    custom_correlation_id = "CID-TEST-TRACE-9999"

    response = client.get(
        "/api/v1/assets/ASSET-777",
        headers={"X-Correlation-ID": custom_correlation_id},
    )

    assert response.status_code == 200
    assert response.headers.get("x-correlation-id") == custom_correlation_id
    body = response.json()
    assert body["success"] is True
    assert body["data"]["asset_id"] == "ASSET-777"


def test_exception_in_sub_router_handled_by_global_middleware_with_envelope(
    client: TestClient,
    mock_dt_command_facade: MagicMock,
):
    mock_dt_command_facade.register_asset.side_effect = BaseSystemException(
        error_code=GlobalErrorCode.ERR_COMMON_FORBIDDEN,
        message="Insufficient permissions to register assets in factory.",
        status_code=403,
    )
    payload = {
        "asset_name": "Prohibited Robot",
        "asset_type": "ROBOT",
        "cad_file_path": "/path/robot.urdf",
    }

    response = client.post("/api/v1/assets", json=payload)

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_COMMON_FORBIDDEN
    assert "Insufficient permissions" in body["message"]


# ==============================================================================
# 3. Lifespan Startup & Shutdown Test
# ==============================================================================
@pytest.mark.asyncio
async def test_app_lifespan_lifecycle_startup_and_shutdown(monkeypatch):
    # Given: 테스트 환경 플래그 해제
    monkeypatch.delenv("TESTING", raising=False)

    from plugins.fast_api.app import lifespan

    mock_app = MagicMock(spec=FastAPI)
    mock_app.dependency_overrides = {}

    with (
        patch("plugins.fast_api.app.rclpy") as mock_rclpy,
        patch("plugins.fast_api.app.MultiThreadedExecutor") as mock_executor_cls,
        patch("plugins.fast_api.app.threading.Thread") as mock_thread_cls,
    ):
        mock_rclpy.ok.return_value = False
        mock_node = MagicMock()
        mock_rclpy.create_node.return_value = mock_node

        mock_executor = MagicMock()
        mock_executor_cls.return_value = mock_executor

        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        # When: lifespan context 직접 진입 및 탈출
        async with lifespan(mock_app):
            # Then: Startup 단계 검증
            mock_rclpy.init.assert_called_once()
            mock_rclpy.create_node.assert_called_once_with("fastapi_inbound_gateway")
            mock_executor.add_node.assert_called_once_with(mock_node)
            mock_thread.start.assert_called_once()
            assert len(mock_app.dependency_overrides) >= 2

        # Then: Shutdown 단계 검증
        mock_executor.shutdown.assert_called_once()
        mock_node.destroy_node.assert_called_once()
