from enum import Enum
from typing import Any


class GlobalErrorCode(str, Enum):
    # Common / Shared Infrastructure
    ERR_COMMON_INVALID_INPUT = "ERR_COMMON_INVALID_INPUT"
    ERR_COMMON_UNAUTHORIZED = "ERR_COMMON_UNAUTHORIZED"
    ERR_COMMON_FORBIDDEN = "ERR_COMMON_FORBIDDEN"
    ERR_COMMON_INTERNAL_ERROR = "ERR_COMMON_INTERNAL_ERROR"
    ERR_DB_CONNECTION_FAILED = "ERR_DB_CONNECTION_FAILED"

    # Asset Twin Domain
    ERR_TWIN_NOT_FOUND = "ERR_TWIN_NOT_FOUND"
    ERR_TWIN_INVALID_SCHEMA = "ERR_TWIN_INVALID_SCHEMA"
    ERR_TWIN_SYNC_OVER_LIMIT = "ERR_TWIN_SYNC_OVER_LIMIT"
    ERR_TWIN_SENSOR_PARSE_FAIL = "ERR_TWIN_SENSOR_PARSE_FAIL"

    # Simulation Domain
    ERR_SIM_INVALID_SCENARIO = "ERR_SIM_INVALID_SCENARIO"
    ERR_SIM_COLLISION_DETECTED = "ERR_SIM_COLLISION_DETECTED"
    ERR_SIM_IPC_TIMEOUT = "ERR_SIM_IPC_TIMEOUT"
    ERR_SIM_RECOVER_EVAL_FAILED = "ERR_SIM_RECOVER_EVAL_FAILED"
    ERR_SIM_RESOURCE_EXHAUSTED = "ERR_SIM_RESOURCE_EXHAUSTED"
    ERR_SIM_PHYSICS_STEP_ERROR = "ERR_SIM_PHYSICS_STEP_ERROR"

    # Edge Control Domain
    ERR_EDGE_COMM_TIMEOUT = "ERR_EDGE_COMM_TIMEOUT"
    ERR_EDGE_FAILSAFE_TRIGGERED = "ERR_EDGE_FAILSAFE_TRIGGERED"
    ERR_EDGE_INTERLOCK_RESET_DENIED = "ERR_EDGE_INTERLOCK_RESET_DENIED"
    ERR_EDGE_DDS_INIT_FAIL = "ERR_EDGE_DDS_INIT_FAIL"

    # B2B & KPI Domain
    ERR_B2B_API_FAILURE = "ERR_B2B_API_FAILURE"
    ERR_B2B_INVALID_QUOTE = "ERR_B2B_INVALID_QUOTE"
    ERR_KPI_DB_TIMEOUT = "ERR_KPI_DB_TIMEOUT"
    ERR_KPI_SIM_NOT_FOUND = "ERR_KPI_SIM_NOT_FOUND"

    # Shared Memory
    ERR_IPC_SHARED_MEMORY_ERROR = "ERR_IPC_SHARED_MEMORY_ERROR"


ERROR_CODE_METADATA: dict[GlobalErrorCode, dict[str, Any]] = {
    # 1. Common / Shared Infrastructure
    GlobalErrorCode.ERR_COMMON_INVALID_INPUT: {
        "status": 400,
        "msg": "Request DTO validation failed or required fields are missing.",
    },
    GlobalErrorCode.ERR_COMMON_UNAUTHORIZED: {
        "status": 401,
        "msg": "JWT token is missing, expired, or signature verification failed.",
    },
    GlobalErrorCode.ERR_COMMON_FORBIDDEN: {
        "status": 403,
        "msg": "Insufficient RBAC role level or unauthorized cross-tenant data access attempt.",
    },
    GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR: {
        "status": 500,
        "msg": "An unexpected internal server error occurred.",
    },
    GlobalErrorCode.ERR_DB_CONNECTION_FAILED: {
        "status": 500,
        "msg": "Database connection failed or connection pool exhausted.",
    },
    GlobalErrorCode.ERR_IPC_SHARED_MEMORY_ERROR: {
        "status": 500,
        "msg": "POSIX Shared Memory or IPC subsystem operation failed.",
    },
    # 2. Asset Twin Domain
    GlobalErrorCode.ERR_TWIN_NOT_FOUND: {
        "status": 404,
        "msg": "The requested AAS asset or 3D layout does not exist.",
    },
    GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA: {
        "status": 400,
        "msg": "AAS or kinematic metadata schema validation violation.",
    },
    GlobalErrorCode.ERR_TWIN_SYNC_OVER_LIMIT: {
        "status": 422,
        "msg": "Cyber-physical synchronization error rate exceeded the allowable threshold (5.0%).",
    },
    GlobalErrorCode.ERR_TWIN_SENSOR_PARSE_FAIL: {
        "status": 500,
        "msg": "Sensor log parsing or computation error.",
    },
    # 3. Simulation Domain
    GlobalErrorCode.ERR_SIM_INVALID_SCENARIO: {
        "status": 400,
        "msg": "Simulation scenario validation failed or baseline is unspecified.",
    },
    GlobalErrorCode.ERR_SIM_COLLISION_DETECTED: {
        "status": 409,
        "msg": "Physical collision or deadlock detected during MuJoCo engine computation.",
    },
    GlobalErrorCode.ERR_SIM_IPC_TIMEOUT: {
        "status": 500,
        "msg": "POSIX SHM synchronization timeout between C++ physics and RL engine (> 1ms).",
    },
    GlobalErrorCode.ERR_SIM_RECOVER_EVAL_FAILED: {
        "status": 422,
        "msg": "No alternative recovery path found.",
    },
    GlobalErrorCode.ERR_SIM_RESOURCE_EXHAUSTED: {
        "status": 503,
        "msg": "GPU VRAM memory consumption exceeded the threshold (4.2GB).",
    },
    GlobalErrorCode.ERR_SIM_PHYSICS_STEP_ERROR: {
        "status": 500,
        "msg": "Numerical instability or physics step simulation computation failure in MuJoCo engine.",
    },
    # 4. Edge Control Domain
    GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT: {
        "status": 504,
        "msg": "Local OT/FastDDS communication packet reception timeout (> 100ms).",
    },
    GlobalErrorCode.ERR_EDGE_FAILSAFE_TRIGGERED: {
        "status": 503,
        "msg": "Safety threshold exceeded; Failsafe E-Stop triggered within 100ms.",
    },
    GlobalErrorCode.ERR_EDGE_INTERLOCK_RESET_DENIED: {
        "status": 409,
        "msg": "Interlock reset request was denied due to unresolved safety preconditions or active faults.",
    },
    GlobalErrorCode.ERR_EDGE_DDS_INIT_FAIL: {
        "status": 500,
        "msg": "Failed to initialize FastDDS domain participant, publisher, or subscriber entities.",
    },
    # 5. B2B & KPI Domain
    GlobalErrorCode.ERR_B2B_API_FAILURE: {
        "status": 502,
        "msg": "External B2B marketplace integration failure or timeout.",
    },
    GlobalErrorCode.ERR_B2B_INVALID_QUOTE: {
        "status": 422,
        "msg": "External marketplace response quote schema mismatch.",
    },
    GlobalErrorCode.ERR_KPI_DB_TIMEOUT: {
        "status": 500,
        "msg": "InfluxDB time-series query latency or disconnection.",
    },
    GlobalErrorCode.ERR_KPI_SIM_NOT_FOUND: {
        "status": 404,
        "msg": "Target simulation result data does not exist.",
    },
}
