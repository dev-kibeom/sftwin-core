#pragma once

namespace sftwin::edge_control::anomaly_failsafe::domain {

enum class EdgeEngineState {
    ACTIVE_MONITORING,
    INTERLOCK_ENGAGED,
    RECOVERY_PENDING
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
