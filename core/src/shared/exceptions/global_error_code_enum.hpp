#pragma once

#include <string>
#include <string_view>

namespace sftwin::shared {

enum class GlobalErrorCode {
    // 1. Common / Shared Infrastructure
    ERR_COMMON_INVALID_INPUT,
    ERR_COMMON_UNAUTHORIZED,
    ERR_COMMON_FORBIDDEN,
    ERR_COMMON_INTERNAL_ERROR,
    ERR_DB_CONNECTION_FAILED,
    ERR_IPC_SHARED_MEMORY_ERROR,

    // 2. Asset Twin Domain
    ERR_TWIN_NOT_FOUND,
    ERR_TWIN_INVALID_SCHEMA,
    ERR_TWIN_SYNC_OVER_LIMIT,
    ERR_TWIN_SENSOR_PARSE_FAIL,

    // 3. Simulation Domain
    ERR_SIM_INVALID_SCENARIO,
    ERR_SIM_COLLISION_DETECTED,
    ERR_SIM_IPC_TIMEOUT,
    ERR_SIM_RECOVER_EVAL_FAILED,
    ERR_SIM_RESOURCE_EXHAUSTED,
    ERR_SIM_PHYSICS_STEP_ERROR,

    // 4. Edge Control Domain
    ERR_EDGE_COMM_TIMEOUT,
    ERR_EDGE_FAILSAFE_TRIGGERED,
    ERR_EDGE_INTERLOCK_RESET_DENIED,
    ERR_EDGE_DDS_INIT_FAIL,

    // 5. B2B & KPI Domain
    ERR_B2B_API_FAILURE,
    ERR_B2B_INVALID_QUOTE,
    ERR_KPI_DB_TIMEOUT,
    ERR_KPI_SIM_NOT_FOUND
};

struct ErrorCodeMetadata {
    int status;
    std::string_view msg;
};

// Enum -> string_view
constexpr std::string_view toString(GlobalErrorCode code) noexcept {
    switch (code) {
        case GlobalErrorCode::ERR_COMMON_INVALID_INPUT:       return "ERR_COMMON_INVALID_INPUT";
        case GlobalErrorCode::ERR_COMMON_UNAUTHORIZED:        return "ERR_COMMON_UNAUTHORIZED";
        case GlobalErrorCode::ERR_COMMON_FORBIDDEN:           return "ERR_COMMON_FORBIDDEN";
        case GlobalErrorCode::ERR_COMMON_INTERNAL_ERROR:      return "ERR_COMMON_INTERNAL_ERROR";
        case GlobalErrorCode::ERR_DB_CONNECTION_FAILED:       return "ERR_DB_CONNECTION_FAILED";
        case GlobalErrorCode::ERR_IPC_SHARED_MEMORY_ERROR:     return "ERR_IPC_SHARED_MEMORY_ERROR";

        case GlobalErrorCode::ERR_TWIN_NOT_FOUND:             return "ERR_TWIN_NOT_FOUND";
        case GlobalErrorCode::ERR_TWIN_INVALID_SCHEMA:         return "ERR_TWIN_INVALID_SCHEMA";
        case GlobalErrorCode::ERR_TWIN_SYNC_OVER_LIMIT:        return "ERR_TWIN_SYNC_OVER_LIMIT";
        case GlobalErrorCode::ERR_TWIN_SENSOR_PARSE_FAIL:      return "ERR_TWIN_SENSOR_PARSE_FAIL";

        case GlobalErrorCode::ERR_SIM_INVALID_SCENARIO:       return "ERR_SIM_INVALID_SCENARIO";
        case GlobalErrorCode::ERR_SIM_COLLISION_DETECTED:     return "ERR_SIM_COLLISION_DETECTED";
        case GlobalErrorCode::ERR_SIM_IPC_TIMEOUT:            return "ERR_SIM_IPC_TIMEOUT";
        case GlobalErrorCode::ERR_SIM_RECOVER_EVAL_FAILED:    return "ERR_SIM_RECOVER_EVAL_FAILED";
        case GlobalErrorCode::ERR_SIM_RESOURCE_EXHAUSTED:     return "ERR_SIM_RESOURCE_EXHAUSTED";
        case GlobalErrorCode::ERR_SIM_PHYSICS_STEP_ERROR: return "ERR_SIM_PHYSICS_STEP_ERROR";

        case GlobalErrorCode::ERR_EDGE_COMM_TIMEOUT:          return "ERR_EDGE_COMM_TIMEOUT";
        case GlobalErrorCode::ERR_EDGE_FAILSAFE_TRIGGERED:    return "ERR_EDGE_FAILSAFE_TRIGGERED";
        case GlobalErrorCode::ERR_EDGE_INTERLOCK_RESET_DENIED: return "ERR_EDGE_INTERLOCK_RESET_DENIED";
        case GlobalErrorCode::ERR_EDGE_DDS_INIT_FAIL: return "ERR_EDGE_DDS_INIT_FAIL";

        case GlobalErrorCode::ERR_B2B_API_FAILURE:            return "ERR_B2B_API_FAILURE";
        case GlobalErrorCode::ERR_B2B_INVALID_QUOTE:          return "ERR_B2B_INVALID_QUOTE";
        case GlobalErrorCode::ERR_KPI_DB_TIMEOUT:             return "ERR_KPI_DB_TIMEOUT";
        case GlobalErrorCode::ERR_KPI_SIM_NOT_FOUND:          return "ERR_KPI_SIM_NOT_FOUND";
        default:                                              return "UNKNOWN_ERROR";
    }
}

// ADL(Argument Dependent Lookup) 지원을 위한 to_string
inline std::string to_string(GlobalErrorCode code) {
    return std::string(toString(code));
}

// Enum -> Metadata
constexpr ErrorCodeMetadata getMetadata(GlobalErrorCode code) noexcept {
    switch (code) {
        // 1. Common / Shared Infrastructure
        case GlobalErrorCode::ERR_COMMON_INVALID_INPUT:
            return {400, "Request DTO validation failed or required fields are missing."};
        case GlobalErrorCode::ERR_COMMON_UNAUTHORIZED:
            return {401, "JWT token is missing, expired, or signature verification failed."};
        case GlobalErrorCode::ERR_COMMON_FORBIDDEN:
            return {403, "Insufficient RBAC role level or unauthorized cross-tenant data access attempt."};
        case GlobalErrorCode::ERR_COMMON_INTERNAL_ERROR:
            return {500, "An unexpected internal server error occurred."};
        case GlobalErrorCode::ERR_DB_CONNECTION_FAILED:
            return {500, "Database connection failed or connection pool exhausted."};
        case GlobalErrorCode::ERR_IPC_SHARED_MEMORY_ERROR:
            return {500, "POSIX Shared Memory or IPC subsystem operation failed."};

        // 2. Asset Twin Domain
        case GlobalErrorCode::ERR_TWIN_NOT_FOUND:
            return {404, "The requested AAS asset or 3D layout does not exist."};
        case GlobalErrorCode::ERR_TWIN_INVALID_SCHEMA:
            return {400, "AAS or kinematic metadata schema validation violation."};
        case GlobalErrorCode::ERR_TWIN_SYNC_OVER_LIMIT:
            return {422, "Cyber-physical synchronization error rate exceeded the allowable threshold (5.0%)."};
        case GlobalErrorCode::ERR_TWIN_SENSOR_PARSE_FAIL:
            return {500, "Sensor log parsing or computation error."};

        // 3. Simulation Domain
        case GlobalErrorCode::ERR_SIM_INVALID_SCENARIO:
            return {400, "Simulation scenario validation failed or baseline is unspecified."};
        case GlobalErrorCode::ERR_SIM_COLLISION_DETECTED:
            return {409, "Physical collision or deadlock detected during MuJoCo engine computation."};
        case GlobalErrorCode::ERR_SIM_IPC_TIMEOUT:
            return {500, "POSIX SHM synchronization timeout between C++ physics and RL engine (> 1ms)."};
        case GlobalErrorCode::ERR_SIM_RECOVER_EVAL_FAILED:
            return {422, "No alternative recovery path found."};
        case GlobalErrorCode::ERR_SIM_RESOURCE_EXHAUSTED:
            return {503, "GPU VRAM memory consumption exceeded the threshold (4.2GB)."};
        case GlobalErrorCode::ERR_SIM_PHYSICS_STEP_ERROR:
            return {500, "Numerical instability or physics step simulation computation failure in MuJoCo engine."};

        // 4. Edge Control Domain
        case GlobalErrorCode::ERR_EDGE_COMM_TIMEOUT:
            return {504, "Local OT/FastDDS communication packet reception timeout (> 100ms)."};
        case GlobalErrorCode::ERR_EDGE_FAILSAFE_TRIGGERED:
            return {503, "Safety threshold exceeded; Failsafe E-Stop triggered within 100ms."};
        case GlobalErrorCode::ERR_EDGE_INTERLOCK_RESET_DENIED: // 추가
            return {409, "Interlock reset request was denied due to unresolved safety preconditions or active faults."};
        case GlobalErrorCode::ERR_EDGE_DDS_INIT_FAIL:
             return {500, "Failed to initialize FastDDS domain participant, publisher, or subscriber entities."};

        // 5. B2B & KPI Domain
        case GlobalErrorCode::ERR_B2B_API_FAILURE:
            return {502, "External B2B marketplace integration failure or timeout."};
        case GlobalErrorCode::ERR_B2B_INVALID_QUOTE:
            return {422, "External marketplace response quote schema mismatch."};
        case GlobalErrorCode::ERR_KPI_DB_TIMEOUT:
            return {500, "InfluxDB time-series query latency or disconnection."};
        case GlobalErrorCode::ERR_KPI_SIM_NOT_FOUND:
            return {404, "Target simulation result data does not exist."};

        default:
            return {500, "Unknown error occurred."};
    }
}

}  // namespace sftwin::shared
