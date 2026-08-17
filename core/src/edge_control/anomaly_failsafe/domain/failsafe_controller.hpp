#pragma once

#include <cstdint>

#include "../domain/failsafe_rule.hpp"
#include "../domain/value_objects/evaluation_result.hpp"
#include "../domain/value_objects/telemetry_snapshot.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

class FailsafeController {
   public:
    explicit FailsafeController(const FailsafeRule& rule) : _rule(rule) {}

    [[nodiscard]] EvaluationResult check_violations(const TelemetrySnapshot& snapshot) const;

   private:
    FailsafeRule _rule;
    [[nodiscard]] uint64_t _get_current_time_ns() const;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
