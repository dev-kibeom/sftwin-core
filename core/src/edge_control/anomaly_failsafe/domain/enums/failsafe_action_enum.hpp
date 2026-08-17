#pragma once

namespace sftwin::edge_control::anomaly_failsafe::domain {

enum class FailsafeActionEnum {
    NONE = 0,
    ESTOP = 1,
    PAUSE = 2,
    BYPASS = 3,
    RESUME = 4
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
