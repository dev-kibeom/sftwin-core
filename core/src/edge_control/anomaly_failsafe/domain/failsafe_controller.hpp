// core/src/edge_control/anomaly_failsafe/domain/failsafe_controller.hpp
#pragma once
#include <string>
#include <vector>
#include <cstdint>

#include "failsafe_rule.hpp"
#include "value_objects/telemetry_snapshot.hpp"
#include "value_objects/evaluation_result.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

class FailsafeController {
   private:
    FailsafeRule _rule;
    uint64_t _get_current_time_ns() const;

   public:
    explicit FailsafeController(const FailsafeRule& rule) : _rule(rule) {}

    // Ports/DTO를 완벽히 배제하고 순수 Domain VO만 받아서 규칙 검증
    EvaluationResult check_violations(const TelemetrySnapshot& snapshot);
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
