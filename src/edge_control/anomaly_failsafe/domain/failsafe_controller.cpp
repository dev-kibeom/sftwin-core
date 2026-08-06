#include "failsafe_controller.hpp"

#include "src/edge_control/common/utils/time_provider.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

uint64_t FailsafeController::_get_current_time_ns() const {
    return common::utils::TimeProvider::get_steady_time_ns();
}

float FailsafeController::_calculate_distance(const sftwin::telemetry::DetectedObject& obj) const {
    // 임시 구현: bbox 크기 또는 별도 속성을 통한 거리 추정 로직 대체
    // 데모 및 단위 테스트를 위해 Bounding Box의 너비(width)를 역산하여 거리로 취급합니다.
    if (obj.bbox_size() >= 3) {
        return obj.bbox(2);  // 인덱스 2를 임시로 거리(Distance) 값으로 사용
    }
    return 999.0f;
}

EvaluationResult FailsafeController::check_violations(
    const sftwin::edge_control::realtime_telemetry::dtos::TelemetryPacketDto& telemetry) {
    const auto& proto = telemetry.get_proto();

    // 1. 통신 지연 평가 (HEARTBEAT_LOSS)
    uint64_t current_time = _get_current_time_ns();
    if (current_time > proto.timestamp_ns() &&
        (current_time - proto.timestamp_ns()) > _rule.heartbeat_timeout_ns) {
        return {FailsafeActionEnum::ESTOP, "HEARTBEAT_LOSS"};
    }

    // 2. 물리 토크 초과 평가 (TORQUE_EXCEEDED)
    for (int i = 0; i < proto.joint_torques_size(); ++i) {
        if (proto.joint_torques(i) > _rule.max_torque_limit_nm) {
            return {FailsafeActionEnum::ESTOP, "TORQUE_EXCEEDED"};
        }
    }

    // 3. 비전 침입 평가 (VISION_INTRUSION)
    bool requires_bypass = false;
    for (int i = 0; i < proto.detected_objects_size(); ++i) {
        float distance = _calculate_distance(proto.detected_objects(i));
        if (distance < _rule.vision_critical_distance_m) {
            return {FailsafeActionEnum::ESTOP, "CRITICAL_INTRUSION"};
        } else if (distance < _rule.vision_warning_distance_m) {
            requires_bypass = true;  // 주의 구역 감지 (조기 리턴하지 않고 끝까지 검사)
        }
    }

    if (requires_bypass) {
        return {FailsafeActionEnum::BYPASS, "WARNING_INTRUSION"};
    }

    // 4. AI 복원 오차 평가 (AI_RECONSTRUCTION_ERR)
    if (proto.has_anomaly_score() && proto.anomaly_score() > _rule.max_ai_anomaly_score) {
        return {FailsafeActionEnum::ESTOP, "AI_RECONSTRUCTION_ERR"};
    }

    // 정상 통과
    return {FailsafeActionEnum::NONE, "OK"};
}

}  // namespace sftwin::edge_control::anomaly_failsafe::domain