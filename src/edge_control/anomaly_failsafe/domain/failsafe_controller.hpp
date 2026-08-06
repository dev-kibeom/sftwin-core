#pragma once
#include <string>

#include "src/edge_control/anomaly_failsafe/domain/failsafe_action_enum.hpp"
#include "src/edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "src/edge_control/realtime_telemetry/dtos/telemetry_packet_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

struct EvaluationResult {
    FailsafeActionEnum action;
    std::string reason;
};

class FailsafeController {
   private:
    FailsafeRule _rule;
    uint64_t _get_current_time_ns() const;
    float _calculate_distance(const sftwin::telemetry::DetectedObject& obj) const;

   public:
    explicit FailsafeController(const FailsafeRule& rule) : _rule(rule) {}

    // 규칙 엔진: Guard Clause 패턴을 통한 조기 리턴(Early Return) 평가
    EvaluationResult check_violations(const dtos::TelemetryPacketDto& telemetry);
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain