#include "../domain/failsafe_controller.hpp"

#include "edge_control/common/utils/time_provider.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

uint64_t FailsafeController::_get_current_time_ns() const {
    return TimeProvider::get_steady_time_ns();
}

EvaluationResult FailsafeController::check_violations(const TelemetrySnapshot& snapshot) const {
    const uint64_t current_time = _get_current_time_ns();
    if (current_time > snapshot.timestamp_ns &&
        (current_time - snapshot.timestamp_ns) > _rule.heartbeat_timeout_ns) {
        return {FailsafeActionEnum::ESTOP, "HEARTBEAT_LOSS"};
    }

    for (const float torque : snapshot.joint_torques) {
        if (torque > _rule.max_torque_limit_nm) {
            return {FailsafeActionEnum::ESTOP, "TORQUE_EXCEEDED"};
        }
    }

    if (snapshot.closest_object_distance_m < _rule.vision_critical_distance_m) {
        return {FailsafeActionEnum::ESTOP, "CRITICAL_INTRUSION"};
    }

    if (snapshot.closest_object_distance_m < _rule.vision_warning_distance_m) {
        return {FailsafeActionEnum::BYPASS, "WARNING_INTRUSION"};
    }

    if (snapshot.ai_anomaly_score > _rule.max_ai_anomaly_score) {
        return {FailsafeActionEnum::ESTOP, "AI_RECONSTRUCTION_ERR"};
    }

    return {FailsafeActionEnum::NONE, "OK"};
}

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
