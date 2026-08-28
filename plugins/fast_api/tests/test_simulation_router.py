# File: plugins/fast_api/tests/test_simulation_router.py

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from polyfactory.factories.dataclass_factory import DataclassFactory
from shared.context.user_context import UserContext
from shared.enums.simulation_state_enum import SimulationState
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole
from simulation.contracts.dtos.optimized_asset_placement_dto import (
    OptimizedAssetPlacementDto,
)
from simulation.contracts.dtos.sim_result_dto import SimResultDto
from simulation.contracts.dtos.simulation_status_dto import (
    SimulationStatusDto,
)
from simulation.fault_recovery.application.inject_fault.inject_fault_result_dto import (
    InjectFaultResultDto,
)
from simulation.fault_recovery.domain.failsafe_recovery_policy.safety_action_enum import (
    SafetyAction,
)

from plugins.fast_api.dependencies.auth import get_current_user_context
from plugins.fast_api.dependencies.facades import (
    get_simulation_command_facade,
    get_simulation_query_facade,
)
from plugins.fast_api.middlewares.exception_handler import (
    register_exception_handlers,
)
from plugins.fast_api.routers.simulation_router import (
    router as simulation_router,
)


# --- Polyfactory Factories ---
class SimResultDtoFactory(DataclassFactory[SimResultDto]):
    __model__ = SimResultDto


class InjectFaultResultDtoFactory(DataclassFactory[InjectFaultResultDto]):
    __model__ = InjectFaultResultDto


class OptimizedAssetPlacementDtoFactory(DataclassFactory[OptimizedAssetPlacementDto]):
    __model__ = OptimizedAssetPlacementDto


class SimulationStatusDtoFactory(DataclassFactory[SimulationStatusDto]):
    __model__ = SimulationStatusDto


# --- Test Fixtures ---
@pytest.fixture
def mock_sim_command_facade():
    return MagicMock()


@pytest.fixture
def mock_sim_query_facade():
    return MagicMock()


@pytest.fixture
def mock_user_context():
    return UserContext(
        user_id="USR-303",
        username="sim_operator",
        company_id="COMP-A",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FAC-01"],
        is_edge_authenticated=False,
    )


@pytest.fixture
def app(
    mock_sim_command_facade,
    mock_sim_query_facade,
    mock_user_context,
) -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    test_app.include_router(simulation_router, prefix="/api/v1")

    test_app.dependency_overrides[get_current_user_context] = lambda: mock_user_context
    test_app.dependency_overrides[get_simulation_command_facade] = lambda: (
        mock_sim_command_facade
    )
    test_app.dependency_overrides[get_simulation_query_facade] = lambda: (
        mock_sim_query_facade
    )

    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ==============================================================================
# 1. Run FMS Simulation Tests
# ==============================================================================
def test_run_fms_simulation_success(
    client: TestClient,
    mock_sim_command_facade: MagicMock,
    mock_user_context: UserContext,
):
    # Given
    mock_result = SimResultDtoFactory.build(
        scenario_id="SCENARIO-001",
        is_success=True,
        collision_count=0,
        estimated_cycle_time_sec=14.5,
    )
    mock_sim_command_facade.run_fms_simulation.return_value = mock_result
    payload = {
        "scenario_id": "SCENARIO-001",
        "baseline_id": "BASE-001",
        "assets": [
            {
                "asset_name": "ROBOT_ARM_01",
                "asset_type": "ROBOT",
                "kinematics_metadata": {"degrees_of_freedom": 6, "dh_parameters": {}},
            }
        ],
        "task_waypoints": [
            {
                "asset_id": "ROBOT_ARM_01",
                "position_x": 10.0,
                "position_y": 5.0,
                "position_z": 0.0,
                "velocity": 1.0,
                "time_sec": 2.0,
            }
        ],
        "max_duration_sec": 30.0,
    }

    # When
    response = client.post("/api/v1/simulations/run", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "SUCCESS"
    assert body["data"]["scenario_id"] == "SCENARIO-001"
    assert body["data"]["is_success"] is True
    assert body["data"]["collision_count"] == 0

    mock_sim_command_facade.run_fms_simulation.assert_called_once()
    called_args, _ = mock_sim_command_facade.run_fms_simulation.call_args
    passed_dto, passed_ctx = called_args
    assert passed_ctx == mock_user_context
    assert passed_dto.scenario_id == "SCENARIO-001"
    assert passed_dto.baseline_id == "BASE-001"
    assert len(passed_dto.assets) == 1
    assert passed_dto.assets[0].company_id == mock_user_context.company_id


def test_run_fms_simulation_collision_detected_returns_409(
    client: TestClient,
    mock_sim_command_facade: MagicMock,
):
    # Given
    mock_sim_command_facade.run_fms_simulation.side_effect = BaseSystemException(
        error_code=GlobalErrorCode.ERR_SIM_COLLISION_DETECTED,
        message="Robot joint collision detected with adjacent structure.",
        status_code=409,
    )
    payload = {
        "scenario_id": "SCENARIO-001",
        "baseline_id": "BASE-001",
        "assets": [],
        "task_waypoints": [],
        "max_duration_sec": 30.0,
    }

    # When
    response = client.post("/api/v1/simulations/run", json=payload)

    # Then
    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["code"] == GlobalErrorCode.ERR_SIM_COLLISION_DETECTED
    assert "Robot joint collision detected" in body["message"]


# ==============================================================================
# 2. Inject Fault & Recovery Tests
# ==============================================================================
def test_inject_fault_success(
    client: TestClient,
    mock_sim_command_facade: MagicMock,
    mock_user_context: UserContext,
):
    # Given
    mock_result = InjectFaultResultDtoFactory.build(
        scenario_id="AMR_01",
        action=SafetyAction.EXECUTE_BYPASS_RECOVERY,
        reason="Obstacle detected.",
        requires_bypass_planning=True,
    )
    mock_sim_command_facade.inject_fault.return_value = mock_result
    payload = {
        "fault_type": "OBSTACLE_APPEARANCE",
        "target": "AMR_01",
        "trigger_time_sec": 5.0,
        "obstacle_distance_m": 1.2,
    }

    # When
    response = client.post("/api/v1/simulations/faults/inject", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["scenario_id"] == "AMR_01"
    assert body["data"]["action"] == SafetyAction.EXECUTE_BYPASS_RECOVERY.value
    assert body["data"]["requires_bypass_planning"] is True

    mock_sim_command_facade.inject_fault.assert_called_once()
    called_args, _ = mock_sim_command_facade.inject_fault.call_args
    passed_dto, passed_ctx = called_args
    assert passed_ctx == mock_user_context
    assert passed_dto.target == "AMR_01"
    assert passed_dto.fault_type == "OBSTACLE_APPEARANCE"


def test_simulate_fault_recovery_success(
    client: TestClient,
    mock_sim_command_facade: MagicMock,
    mock_user_context: UserContext,
):
    # Given
    mock_sim_result = SimResultDtoFactory.build(
        scenario_id="RECOVERY-SCENARIO-01",
        is_success=True,
        collision_count=0,
    )
    mock_sim_command_facade.simulate_fault_recovery_scenario.return_value = (
        mock_sim_result
    )

    payload = {
        "fault_schema": {
            "fault_type": "CONVEYOR_JAM",
            "target": "CONVEYOR_01",
            "trigger_time_sec": 3.0,
            "obstacle_distance_m": 0.0,
        },
        "recovery_schema": {
            "sequence_script": "CONVEYOR_01.CLEAR_JAM(); CONVEYOR_01.RESUME();",
            "device_id": "EDGE_NODE_001",
        },
    }

    # When: FastAPI body injection 처리 방식에 맞춰 단일 json 페이로드로 전송
    response = client.post(
        "/api/v1/simulations/faults/simulate-recovery",
        json=payload,
    )

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["scenario_id"] == "RECOVERY-SCENARIO-01"
    assert body["data"]["is_success"] is True

    mock_sim_command_facade.simulate_fault_recovery_scenario.assert_called_once()


# ==============================================================================
# 3. Optimize Layout Tests
# ==============================================================================
def test_optimize_layout_success(
    client: TestClient,
    mock_sim_command_facade: MagicMock,
    mock_user_context: UserContext,
):
    # Given
    mock_placement = OptimizedAssetPlacementDtoFactory.build(
        asset_id="ROBOT_01",
        pos_x=12.5,
        pos_y=0.0,
        pos_z=0.0,
        rotation_yaw=0.0,
    )
    mock_sim_command_facade.optimize_layout.return_value = [mock_placement]
    payload = {
        "assets": [{"asset_id": "ROBOT_01", "target_pos_x": 12.5}],
        "canvas_bounds": {"max_x": 50.0, "max_y": 50.0, "max_z": 10.0},
    }

    # When
    response = client.post("/api/v1/simulations/optimize-layout", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["asset_id"] == "ROBOT_01"
    assert body["data"][0]["pos_x"] == 12.5

    mock_sim_command_facade.optimize_layout.assert_called_once()


# ==============================================================================
# 4. Deploy Sim2Real Tests
# ==============================================================================
def test_deploy_sim2real_success(
    client: TestClient,
    mock_sim_command_facade: MagicMock,
    mock_user_context: UserContext,
):
    # Given
    mock_sim_command_facade.deploy_sim2real_package.return_value = True
    payload = {
        "package_id": "PKG-001",
        "format_type": "VDA5050",
        "config": {
            "mqtt_broker_url": "mqtt://localhost:1883",
            "topic_prefix": "uagv/v2",
            "manufacturer": "SFTWIN_ROBOTICS",
            "serial_number": "AGV-001",
        },
    }

    # When
    response = client.post("/api/v1/simulations/deploy-sim2real", json=payload)

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] is True

    mock_sim_command_facade.deploy_sim2real_package.assert_called_once()
    called_args, _ = mock_sim_command_facade.deploy_sim2real_package.call_args
    passed_dto, passed_ctx = called_args
    assert passed_ctx == mock_user_context
    assert passed_dto.package_id == "PKG-001"


# ==============================================================================
# 5. Get Simulation Status Tests
# ==============================================================================
def test_get_simulation_status_success(
    client: TestClient,
    mock_sim_query_facade: MagicMock,
    mock_user_context: UserContext,
):
    # Given
    mock_status = SimulationStatusDtoFactory.build(
        scenario_id="SCENARIO-001",
        status=SimulationState.COMPLETED,
        progress_percent=100.0,
    )
    mock_sim_query_facade.get_simulation_status.return_value = mock_status

    # When
    response = client.get("/api/v1/simulations/SCENARIO-001/status")

    # Then
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["scenario_id"] == "SCENARIO-001"
    assert body["data"]["status"] == SimulationState.COMPLETED.value
    assert body["data"]["progress_percent"] == 100.0

    mock_sim_query_facade.get_simulation_status.assert_called_once_with(
        "SCENARIO-001", mock_user_context
    )
