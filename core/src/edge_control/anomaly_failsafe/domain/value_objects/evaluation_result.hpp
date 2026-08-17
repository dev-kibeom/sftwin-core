#pragma once

#include <string>

#include "../enums/failsafe_action_enum.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

struct EvaluationResult {
    FailsafeActionEnum action{FailsafeActionEnum::NONE};
    std::string reason{"OK"};
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
