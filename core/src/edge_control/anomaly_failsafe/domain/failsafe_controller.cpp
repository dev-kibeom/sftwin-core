#include "src/edge_control/anomaly_failsafe/domain/failsafe_controller.hpp"
#include "src/edge_control/common/utils/time_provider.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

uint64_t FailsafeController::_get_current_time_ns() const {
    return TimeProvider::get_steady_time_ns();
}

EvaluationResult FailsafeController::check_violations(const TelemetrySnapshot& snapshot) {
    // 1. 통신 지연 평가 (HEARTBEAT_LOSS)
    uint64_t current_time = _get_current_time_ns();
    if (current_time > snapshot.timestamp_ns &&
        (current_time - snapshot.timestamp_ns) > _rule.heartbeat_timeout_ns) {
        return {FailsafeActionEnum::ESTOP, "HEARTBEAT_LOSS"};
    }

    // 2. 물리 토크 초과 평가 (TORQUE_EXCEEDED)
    for (float torque : snapshot.joint_torques) {
        if (torque > _rule.max_torque_limit_nm) {
            return {FailsafeActionEnum::ESTOP, "TORQUE_EXCEEDED"};
        }
    }

    // 3. 비전 침입 평가 (VISION_INTRUSION)
    if (snapshot.closest_object_distance_m < _rule.vision_critical_distance_m) {
        return {FailsafeActionEnum::ESTOP, "CRITICAL_INTRUSION"};
    } else if (snapshot.closest_object_distance_m < _rule.vision_warning_distance_m) {
        return {FailsafeActionEnum::BYPASS, "WARNING_INTRUSION"};
    }

    // 4. AI 복원 오차 평가 (AI_RECONSTRUCTION_ERR)
    if (snapshot.ai_anomaly_score > _rule.max_ai_anomaly_score) {
        return {FailsafeActionEnum::ESTOP, "AI_RECONSTRUCTION_ERR"};
    }

    // 정상 통과
    return {FailsafeActionEnum::NONE, "OK"};
}

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
