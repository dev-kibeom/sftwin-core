#pragma once

#include <cstdint>
#include "evaluation_result.hpp"
#include "failsafe_rule.hpp"
#include "../telemetry_snapshot.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

class FailsafeEvaluator {
   public:
    explicit FailsafeEvaluator(const FailsafeRule& rule) : _rule(rule) {}

    [[nodiscard]] EvaluationResult evaluate_violations(
        const TelemetrySnapshot& snapshot, uint64_t current_time_ns) const;

   private:
    FailsafeRule _rule;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
