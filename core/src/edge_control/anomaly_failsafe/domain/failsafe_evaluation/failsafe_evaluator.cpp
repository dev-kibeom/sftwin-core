#include "failsafe_evaluator.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

EvaluationResult FailsafeEvaluator::evaluate_violations(
    const TelemetrySnapshot& snapshot, uint64_t current_time_ns) const {

    // 1. 통신 지연 (Heartbeat 손실) 판정
    if (current_time_ns > snapshot.timestamp_ns &&
        (current_time_ns - snapshot.timestamp_ns) > _rule.heartbeat_timeout_ns) {
        return {FailsafeAction::ESTOP, "HEARTBEAT_LOSS"};
    }

    // 2. 물리 관절 토크 한계 초과 판정
    for (const float torque : snapshot.joint_torques) {
        if (torque > _rule.max_torque_limit_nm) {
            return {FailsafeAction::ESTOP, "TORQUE_EXCEEDED"};
        }
    }

    // 3. 비전 공간 침범 판정
    if (snapshot.closest_object_distance_m < _rule.vision_critical_distance_m) {
        return {FailsafeAction::ESTOP, "CRITICAL_INTRUSION"};
    }

    if (snapshot.closest_object_distance_m < _rule.vision_warning_distance_m) {
        return {FailsafeAction::BYPASS, "WARNING_INTRUSION"};
    }

    // 4. AI 시계열 이상 점수 초과 판정
    if (snapshot.ai_anomaly_score > _rule.max_ai_anomaly_score) {
        return {FailsafeAction::ESTOP, "AI_RECONSTRUCTION_ERR"};
    }

    return {FailsafeAction::NONE, "OK"};
}

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
