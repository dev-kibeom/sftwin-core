#pragma once

namespace sftwin::edge_control::anomaly_failsafe::domain {

enum class InterlockState {
    RELEASED = 0,
    ENGAGED = 1,
    PENDING_RESET_APPROVAL = 2
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
