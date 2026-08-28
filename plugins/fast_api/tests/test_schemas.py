# File: plugins/fast_api/tests/test_schemas.py

from dataclasses import FrozenInstanceError
from typing import Any

import pytest
from pydantic import ValidationError
from shared.dtos.global_response_dto import GlobalResponseDto

from plugins.fast_api.schemas.enums import (
    ApiTag,
    HttpHeaderKey,
    SignalingMessageType,
)
from plugins.fast_api.schemas.requests import (
    CalibrateDynamicsRequestSchema,
    GenerateDualKpiReportRequestSchema,
    GenerateQuoteRequestSchema,
    OptimizeLayoutRequestSchema,
    RegisterAssetRequestSchema,
    ResetInterlockRequestSchema,
    RunFmsSimulationRequestSchema,
    TriggerManualEstopRequestSchema,
)


# ==============================================================================
# 1. Enums Verification
# ==============================================================================
def test_enums_values_match_specification():
    # Given & When & Then
    assert HttpHeaderKey.AUTHORIZATION.value == "Authorization"
    assert HttpHeaderKey.X_TRACE_ID.value == "X-Trace-Id"
    assert HttpHeaderKey.X_IDEMPOTENCY_KEY.value == "X-Idempotency-Key"

    assert ApiTag.ASSET_LIBRARY.value == "Asset Library"
    assert ApiTag.DIGITAL_TWIN.value == "Digital Twin & Layout"
    assert ApiTag.SIMULATION.value == "Simulation & Deployment"
    assert ApiTag.PROCUREMENT_KPI.value == "B2B Procurement & KPI"
    assert ApiTag.EDGE_CONTROL.value == "Edge Control & Monitoring"
    assert ApiTag.WEBRTC_SIGNALING.value == "WebRTC Video Signaling"

    assert SignalingMessageType.OFFER.value == "OFFER"
    assert SignalingMessageType.ANSWER.value == "ANSWER"
    assert SignalingMessageType.CANDIDATE.value == "CANDIDATE"
    assert SignalingMessageType.CLOSE.value == "CLOSE"


# ==============================================================================
# 2. Asset & Twin Request Schemas (Happy Path & Validations)
# ==============================================================================
def test_register_asset_request_schema_success():
    # Given
    payload = {
        "asset_name": "Robotic Arm Kuka",
        "asset_type": "ROBOT",
        "cad_file_path": "/models/kuka.urdf",
        "kinematics_metadata": {"dof": 6},
        "submodels": {"power": 220},
    }

    # When
    schema = RegisterAssetRequestSchema(**payload)

    # Then
    assert schema.asset_name == "Robotic Arm Kuka"
    assert schema.asset_type == "ROBOT"
    assert schema.cad_file_path == "/models/kuka.urdf"


def test_register_asset_request_schema_empty_name_fails():
    # Given
    invalid_payload: dict[str, Any] = {
        "asset_name": "",
        "asset_type": "ROBOT",
    }

    # When & Then
    with pytest.raises(ValidationError):
        RegisterAssetRequestSchema(**invalid_payload)


def test_calibrate_dynamics_request_schema_tolerance_boundary_validation():
    # Given: Valid payload
    valid_payload = {
        "baseline_id": "BASE_001",
        "source_log_path": "/data/logs/test.csv",
        "target_tolerance_percent": 3.5,
        "max_iterations": 20,
    }
    schema = CalibrateDynamicsRequestSchema(**valid_payload)
    assert schema.target_tolerance_percent == 3.5

    # Edge Case: target_tolerance_percent > 5.0 should fail
    with pytest.raises(ValidationError):
        CalibrateDynamicsRequestSchema(
            baseline_id="BASE_001",
            source_log_path="/data/logs/test.csv",
            target_tolerance_percent=5.1,
        )

    # Edge Case: target_tolerance_percent <= 0.0 should fail
    with pytest.raises(ValidationError):
        CalibrateDynamicsRequestSchema(
            baseline_id="BASE_001",
            source_log_path="/data/logs/test.csv",
            target_tolerance_percent=0.0,
        )


def test_optimize_layout_request_schema_empty_assets_fails():
    # Given
    invalid_payload = {
        "assets": [],
        "canvas_bounds": {"max_x": 50.0, "max_y": 50.0, "max_z": 10.0},
    }

    # When & Then
    with pytest.raises(ValidationError):
        OptimizeLayoutRequestSchema(**invalid_payload)


# ==============================================================================
# 3. Simulation & Edge & Procurement Schemas
# ==============================================================================
def test_run_fms_simulation_request_schema_duration_validation():
    # Given: valid payload
    valid_payload = {
        "scenario_id": "SCENARIO_01",
        "baseline_id": "BASE_001",
        "max_duration_sec": 60.0,
    }
    schema = RunFmsSimulationRequestSchema(**valid_payload)
    assert schema.max_duration_sec == 60.0

    # Edge Case: max_duration_sec > 120.0 should fail
    with pytest.raises(ValidationError):
        RunFmsSimulationRequestSchema(
            scenario_id="SCENARIO_01",
            baseline_id="BASE_001",
            max_duration_sec=120.1,
        )


def test_generate_dual_kpi_report_request_schema_oee_range_validation():
    # Given: Valid payload
    valid_payload = {
        "baseline_oee": 80.5,
        "improved_oee": 92.0,
        "baseline_fpy": 85.0,
        "improved_fpy": 95.0,
        "turnkey_quote_cost": 50000000.0,
    }
    schema = GenerateDualKpiReportRequestSchema(**valid_payload)
    assert schema.baseline_oee == 80.5

    # Edge Case: improved_oee > 100.0 should fail
    with pytest.raises(ValidationError):
        GenerateDualKpiReportRequestSchema(
            baseline_oee=80.5,
            improved_oee=100.5,
            baseline_fpy=85.0,
            improved_fpy=95.0,
            turnkey_quote_cost=50000000.0,
        )


def test_edge_and_procurement_schemas_instantiation():
    # Given & When & Then: E-Stop & Interlock
    estop_schema = TriggerManualEstopRequestSchema(reason="Collision risk")
    assert estop_schema.device_id == "EDGE_NODE_001"

    interlock_schema = ResetInterlockRequestSchema(
        is_field_inspected=True,
        is_manager_approved=True,
    )
    assert interlock_schema.is_field_inspected is True
    assert interlock_schema.is_manager_approved is True

    # Given & When & Then: Quote
    quote_schema = GenerateQuoteRequestSchema(asset_ids=["A1", "A2"])
    assert len(quote_schema.asset_ids) == 2


# ==============================================================================
# 4. Global Envelope DTO Verification (Core Shared DTO)
# ==============================================================================
def test_global_response_dto_creation_and_factory_methods():
    # Given & When: Success response factory
    success_res = GlobalResponseDto.success_response(data="RESULT_DATA", message="OK")

    # Then
    assert success_res.success is True
    assert success_res.code == "SUCCESS"
    assert success_res.data == "RESULT_DATA"
    assert success_res.message == "OK"
    assert success_res.timestamp is not None

    # Given & When: Error response factory
    error_res = GlobalResponseDto.error_response(
        code="ERR_COMMON_INVALID_INPUT", message="Invalid payload"
    )

    # Then
    assert error_res.success is False
    assert error_res.code == "ERR_COMMON_INVALID_INPUT"
    assert error_res.data is None
    assert error_res.message == "Invalid payload"

    # Immutability verification (frozen dataclass)
    with pytest.raises(FrozenInstanceError):
        success_res.success = False
