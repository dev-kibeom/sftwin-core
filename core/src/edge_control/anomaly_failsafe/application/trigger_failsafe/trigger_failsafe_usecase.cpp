#include "trigger_failsafe_usecase.hpp"

#include <algorithm>

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/logging/edge_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

// DTO 타입 간결화를 위한 네임스페이스 Alias (C++17)
using realtime_telemetry::dtos::TelemetryPacketDto;
using realtime_telemetry::dtos::VisionDetectionDto;

TriggerFailsafeUseCase::TriggerFailsafeUseCase(
    std::shared_ptr<ports::IHardwareInterlock> hw_interlock,
    std::shared_ptr<ports::IFailsafePublisher> failsafe_pub,
    std::shared_ptr<ports::IRecoverySequence> recovery,
    const domain::FailsafeRule& rule)
    : _hw_interlock(std::move(hw_interlock)),
      _failsafe_pub(std::move(failsafe_pub)), // 🐛 오타 수정: __failsafe_pub -> _failsafe_pub
      _recovery(std::move(recovery)),
      _controller(rule),
      _current_state(domain::EdgeEngineState::ACTIVE_MONITORING),
      _edge_device_id("EDGE_NODE_001") {}

void TriggerFailsafeUseCase::evaluate_and_trigger(
    const TelemetryPacketDto& telemetry,
    const std::vector<VisionDetectionDto>& vision_detections) {

    if (_current_state != domain::EdgeEngineState::ACTIVE_MONITORING) return;

    // 1. 비전 객체 중 최소 거리(가장 가까운 장애물) 산출
    float min_distance = 999.0f;
    for (const auto& det : vision_detections) {
        if (det.bbox[2] > 0.0f && det.bbox[2] < min_distance) {
            min_distance = det.bbox[2];
        }
    }

    // 2. Ports/DTO -> Domain Value Object 변환
    domain::TelemetrySnapshot snapshot{
        telemetry.device_id(),
        telemetry.timestamp_ns(),
        telemetry.joint_torques(),
        min_distance,
        0.0f  // AI anomaly score
    };

    // 3. 순수 도메인 규칙 검증 및 Failsafe 액션 처리
    const auto result = _controller.check_violations(snapshot);

    if (result.action == domain::FailsafeActionEnum::ESTOP) {
        _hw_interlock->trigger_physical_relay();

        _failsafe_pub->publish("failsafe/estop",
                               dtos::FailsafeCommandDto(telemetry.device_id(), "ESTOP", result.reason));

        _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
        EDGE_LOG_ERROR("Failsafe Auto E-STOP Triggered! Reason: {}", result.reason);

        throw common::exceptions::EdgeSystemException("ERR_EDGE_FAILSAFE_TRIGGERED",
                                                      "Critical safety breach: " + result.reason);
    }

    if (result.action == domain::FailsafeActionEnum::BYPASS) {
        EDGE_LOG_WARN("Bypass triggered due to warning intrusion. Reason: {}", result.reason);
    }
}

void TriggerFailsafeUseCase::trigger_manual_estop(const std::string& reason) {
    if (_current_state != domain::EdgeEngineState::ACTIVE_MONITORING) {
        EDGE_LOG_WARN("Invalid state transition: E-Stop requested but state is not ACTIVE_MONITORING.");
        throw common::exceptions::EdgeSystemException(
            "ERR_COMMON_INVALID_INPUT", "Engine is already interlocked or in recovery.");
    }

    _hw_interlock->trigger_physical_relay();
    _failsafe_pub->publish("failsafe/estop",
                           dtos::FailsafeCommandDto(_edge_device_id, "ESTOP", reason));

    _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
    EDGE_LOG_INFO("Manual E-Stop successfully triggered. State -> INTERLOCK_ENGAGED (Reason: {})", reason);
}

bool TriggerFailsafeUseCase::execute_recovery_sequence(const std::string& script) {
    if (_current_state != domain::EdgeEngineState::INTERLOCK_ENGAGED) {
        EDGE_LOG_WARN("Invalid state transition: Resume requested but engine is not interlocked.");
        throw common::exceptions::EdgeSystemException("ERR_COMMON_INVALID_INPUT",
                                                      "Engine is not in an interlocked state.");
    }

    _current_state = domain::EdgeEngineState::RECOVERY_PENDING;
    EDGE_LOG_INFO("Recovery script received. State -> RECOVERY_PENDING");

    const bool recovery_success = _recovery->execute_recovery_sequence(script);
    if (!recovery_success) {
        EDGE_LOG_ERROR("Recovery sequence execution failed!");
        _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
        return false;
    }

    _current_state = domain::EdgeEngineState::ACTIVE_MONITORING;
    _failsafe_pub->publish("failsafe/resume",
                           dtos::FailsafeCommandDto(_edge_device_id, "RESUME", "RECOVERY_SUCCESS"));

    EDGE_LOG_INFO("Recovery successful. State -> ACTIVE_MONITORING");
    return true;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
