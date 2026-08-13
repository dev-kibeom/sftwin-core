#pragma once

#include <string>
#include <vector>
#include <cstdint>

#include "src/edge_control/anomaly_failsafe/domain/edge_local_enums.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

struct EvaluationResult {
    FailsafeActionEnum action;
    std::string reason;
};

}
