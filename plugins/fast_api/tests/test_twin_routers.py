# File: plugins/fast_api/tests/test_twin_routers.py

from unittest.mock import MagicMock

import pytest
from digital_twin.contracts.dtos.asset_dto import AssetDto
from digital_twin.contracts.dtos.calibrate_dynamics_dto import (
    CalibrateDynamicsResponseDto,
)
from digital_twin.twin_reconstruction.application.get_layout.layout_render_dto import (
    LayoutRenderDto,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.twin_metrics_dto import (
    TwinMetricsDto,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from polyfactory.factories.dataclass_factory import DataclassFactory
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole

from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.facades import (
    get_digital_twin_command_facade,
    get_digital_twin_query_facade,
)
from plugins.fast_api.middlewares.exception_handler import (
    register_exception_handlers,
)
from plugins.fast_api.routers.asset_router import router as asset_router
from plugins.fast_api.routers.digital_twin_router import (
    router as digital_twin_router,
)


# --- Model Factories ---
class AssetDtoFactory(DataclassFactory[AssetDto]):
    __model__ = AssetDto


class LayoutRenderDtoFactory(DataclassFactory[LayoutRenderDto]):
    __model__ = LayoutRenderDto


class TwinMetricsDtoFactory(DataclassFactory[TwinMetricsDto]):
    __model__ = TwinMetricsDto


class CalibrateDynamicsResponseDtoFactory(
    DataclassFactory[CalibrateDynamicsResponseDto]
):
    __model__ = CalibrateDynamicsResponseDto


# --- Test Fixtures ---
@pytest.fixture
def mock_dt_command_facade():
    return MagicMock()


@pytest.fixture
def mock_dt_query_facade():
    return MagicMock()


@pytest.fixture
def mock_user_context():
    return UserContext(
        user_id="USR-101",
        username="twin_creator",
        company_id="COMP-A",
        role=UserRole.CREATOR,
        accessible_factory_ids=["FAC-01"],
        is_edge_authenticated=True,
    )


@pytest.fixture
def app(
    mock_dt_command_facade,
    mock_dt_query_facade,
    mock_user_context,
) -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    test_app.include_router(asset_router, prefix="/api/v1")
    test_app.include_router(digital_twin_router, prefix="/api/v1")

    test_app.dependency_overrides[get_current_user_context] = lambda: mock_user_context
    test_app.dependency_overrides[get_digital_twin_command_facade] = lambda: (
        mock_dt_command_facade
    )
    test_app.dependency_overrides[get_digital_twin_query_facade] = lambda: (
        mock_dt_query_facade
    )

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ==============================================================================
# 1. Asset Router Tests
# ==============================================================================
def test_register_asset_success(
    client: TestClient,
    mock_dt_command_facade: MagicMock,
    mock_user_context: UserContext,
):
    mock_dt_command_facade.register_asset.return_value = "ASSET-999"
    payload = {
        "asset_name": "KUKA KR QUANTEC",
        "asset_type": "ROBOT",
        "cad_file_path": "/models/kuka.urdf",
        "kinematics_metadata": {"dof": 6},
        "submodels": {},
    }

    response = client.post("/api/v1/assets", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "SUCCESS"
    assert body["data"] == "ASSET-999"

    mock_dt_command_facade.register_asset.assert_called_once()
    called_args, _ = mock_dt_command_facade.register_asset.call_args
    passed_dto, passed_ctx = called_args
    assert isinstance(passed_dto, AssetDto)
    assert passed_dto.asset_name == "KUKA KR QUANTEC"
    assert passed_ctx == mock_user_context


def test_get_asset_success(
    client: TestClient,
    mock_dt_query_facade: MagicMock,
    mock_user_context: UserContext,
):
    # 관심 있는 필드만 지정하고 나머지는 Polyfactory가 자동 생성
    mock_asset = AssetDtoFactory.build(
        asset_id="ASSET-101",
        asset_name="CNC Machine 01",
        company_id="COMP-A",
    )
    mock_dt_query_facade.get_asset.return_value = mock_asset

    response = client.get("/api/v1/assets/ASSET-101")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["asset_id"] == "ASSET-101"
    assert body["data"]["asset_name"] == "CNC Machine 01"

    mock_dt_query_facade.get_asset.assert_called_once_with(
        "ASSET-101", mock_user_context
    )


def test_get_asset_not_found_returns_404(
    client: TestClient,
    mock_dt_query_facade: MagicMock,
):
    mock_dt_query_facade.get_asset.side_effect = BaseSystemException(
        error_code=GlobalErrorCode.ERR_TWIN_NOT_FOUND,
        message="Asset not found.",
        status_code=404,
    )

    response = client.get("/api/v1/assets/NON_EXISTENT")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_TWIN_NOT_FOUND


# ==============================================================================
# 2. Digital Twin Router Tests
# ==============================================================================
def test_get_twin_layout_success(
    client: TestClient,
    mock_dt_query_facade: MagicMock,
    mock_user_context: UserContext,
):
    # positions, hotspots 등 불필요한 빈 리스트 선언 생략
    mock_layout = LayoutRenderDtoFactory.build(baseline_id="BASE-001")
    mock_dt_query_facade.get_layout.return_value = mock_layout

    response = client.get("/api/v1/twins/baselines/BASE-001/layout")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["baseline_id"] == "BASE-001"

    mock_dt_query_facade.get_layout.assert_called_once_with(
        "BASE-001", mock_user_context
    )


def test_reconstruct_twin_success(
    client: TestClient,
    mock_dt_command_facade: MagicMock,
    mock_user_context: UserContext,
):
    mock_metrics = TwinMetricsDtoFactory.build(baseline_id="BASE-102")
    mock_dt_command_facade.reconstruct_twin.return_value = mock_metrics
    payload = {
        "baseline_name": "Reconstructed Baseline #1",
        "source_log_path": "/data/logs/factory_run.csv",
    }

    response = client.post("/api/v1/twins/baselines/reconstruct", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["baseline_id"] == "BASE-102"

    mock_dt_command_facade.reconstruct_twin.assert_called_once()


def test_calibrate_dynamics_success(
    client: TestClient,
    mock_dt_command_facade: MagicMock,
    mock_user_context: UserContext,
):
    mock_calibration = CalibrateDynamicsResponseDtoFactory.build(
        baseline_id="BASE-001",
    )
    mock_dt_command_facade.calibrate_dynamics.return_value = mock_calibration
    payload = {
        "baseline_id": "BASE-001",
        "source_log_path": "/data/logs/calibration_log.csv",
        "target_tolerance_percent": 2.0,
        "max_iterations": 15,
        "initial_parameters": {"damping": 0.1},
    }

    response = client.post("/api/v1/twins/baselines/calibrate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["baseline_id"] == "BASE-001"

    mock_dt_command_facade.calibrate_dynamics.assert_called_once()
