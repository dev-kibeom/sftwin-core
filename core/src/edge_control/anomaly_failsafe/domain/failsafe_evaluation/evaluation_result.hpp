#pragma once

#include <string>
#include "failsafe_action_enum.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

struct EvaluationResult {
    FailsafeAction action{FailsafeAction::NONE};
    std::string reason{"OK"};
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
