#include "trigger_failsafe_usecase.hpp"

#include <utility>

#include "edge_control/common/exceptions/edge_system_exception.hpp"
#include "edge_control/common/logging/edge_logger.hpp"
#include "edge_control/ports/inbound/dtos/failsafe_command_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

TriggerFailsafeUseCase::TriggerFailsafeUseCase(
    std::shared_ptr<IHardwareInterlock> hw_interlock,
    std::shared_ptr<IFailsafePublisher> failsafe_pub,
    std::shared_ptr<IRecoverySequence> recovery,
    const domain::FailsafeRule& rule)
    : _hw_interlock(std::move(hw_interlock)),
      _failsafe_pub(std::move(failsafe_pub)),
      _recovery(std::move(recovery)),
      _controller(rule) {}

void TriggerFailsafeUseCase::evaluate_and_trigger(
    const TelemetryPacketDto& telemetry,
    const std::vector<VisionDetectionDto>& vision_detections) {

    if (_current_state != domain::EdgeEngineState::ACTIVE_MONITORING) {
        return;
    }

    const domain::TelemetrySnapshot snapshot{
        telemetry.device_id(),
        telemetry.timestamp_ns(),
        telemetry.joint_torques(),
        _extract_min_distance(vision_detections),
        0.0f
    };

    const auto result = _controller.check_violations(snapshot);

    if (result.action == domain::FailsafeActionEnum::ESTOP) {
        if (_hw_interlock) _hw_interlock->trigger_physical_relay();
        if (_failsafe_pub) {
            _failsafe_pub->publish("failsafe/estop",
                                   FailsafeCommandDto(telemetry.device_id(), "ESTOP", result.reason));
        }

        _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
        EDGE_LOG_ERROR("Failsafe Auto E-STOP Triggered! Reason: {}", result.reason);

        throw EdgeSystemException("ERR_EDGE_FAILSAFE_TRIGGERED",
                                  "Critical safety breach: " + result.reason);
    }

    if (result.action == domain::FailsafeActionEnum::BYPASS) {
        EDGE_LOG_WARN("Bypass triggered due to warning intrusion. Reason: {}", result.reason);
    }
}

void TriggerFailsafeUseCase::trigger_manual_estop(const std::string& reason) {
    if (_current_state != domain::EdgeEngineState::ACTIVE_MONITORING) {
        EDGE_LOG_WARN("Invalid state transition: E-Stop requested but state is not ACTIVE_MONITORING.");
        throw EdgeSystemException("ERR_COMMON_INVALID_INPUT",
                                  "Engine is already interlocked or in recovery.");
    }

    if (_hw_interlock) _hw_interlock->trigger_physical_relay();
    if (_failsafe_pub) {
        _failsafe_pub->publish("failsafe/estop",
                               FailsafeCommandDto(_edge_device_id, "ESTOP", reason));
    }

    _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
    EDGE_LOG_INFO("Manual E-Stop successfully triggered. State -> INTERLOCK_ENGAGED (Reason: {})", reason);
}

bool TriggerFailsafeUseCase::execute_recovery_sequence(const std::string& script) {
    if (_current_state != domain::EdgeEngineState::INTERLOCK_ENGAGED) {
        EDGE_LOG_WARN("Invalid state transition: Resume requested but engine is not interlocked.");
        throw EdgeSystemException("ERR_COMMON_INVALID_INPUT",
                                  "Engine is not in an interlocked state.");
    }

    _current_state = domain::EdgeEngineState::RECOVERY_PENDING;
    EDGE_LOG_INFO("Recovery script received. State -> RECOVERY_PENDING");

    if (!_recovery || !_recovery->execute_recovery_sequence(script)) {
        EDGE_LOG_ERROR("Recovery sequence execution failed!");
        _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
        return false;
    }

    _current_state = domain::EdgeEngineState::ACTIVE_MONITORING;
    if (_failsafe_pub) {
        _failsafe_pub->publish("failsafe/resume",
                               FailsafeCommandDto(_edge_device_id, "RESUME", "RECOVERY_SUCCESS"));
    }

    EDGE_LOG_INFO("Recovery successful. State -> ACTIVE_MONITORING");
    return true;
}

float TriggerFailsafeUseCase::_extract_min_distance(
    const std::vector<VisionDetectionDto>& detections) const noexcept {
    float min_dist = 999.0f;
    for (const auto& det : detections) {
        if (det.bbox[2] > 0.0f && det.bbox[2] < min_dist) {
            min_dist = det.bbox[2];
        }
    }
    return min_dist;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
