#include "trigger_failsafe_usecase.hpp"

#include <utility>

#include "edge_control/ports/inbound/dtos/failsafe_command_dto.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/logger/global_system_logger.hpp"
#include "shared/utils/time_provider.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
using namespace sftwin::shared;

TriggerFailsafeUseCase::TriggerFailsafeUseCase(
    std::shared_ptr<IHardwareInterlock> hw_interlock,
    std::shared_ptr<IFailsafePublisher> failsafe_pub,
    std::shared_ptr<IRecoverySequence> recovery,
    const domain::FailsafeRule& rule)
    : _hw_interlock(std::move(hw_interlock)),
      _failsafe_pub(std::move(failsafe_pub)),
      _recovery(std::move(recovery)),
      _evaluator(rule) {}

void TriggerFailsafeUseCase::evaluate_and_trigger(
    const TelemetryPacketDto& telemetry,
    const std::vector<VisionDetectionDto>& vision_detections) {
    GLOBAL_LOG_DEBUG("Executing TriggerFailsafeUseCase::evaluate_and_trigger");

    if (_current_state != domain::InterlockState::RELEASED) {
        return;
    }

    const domain::TelemetrySnapshot snapshot{
        telemetry.device_id(),
        telemetry.timestamp_ns(),
        telemetry.joint_torques(),
        _extract_min_distance(vision_detections),
        0.0f
    };

    const uint64_t current_time_ns = GlobalTimeProvider::get_steady_time_ns();
    const auto result = _evaluator.evaluate_violations(snapshot, current_time_ns);

    if (result.action == domain::FailsafeAction::ESTOP) {
        if (_hw_interlock) _hw_interlock->trigger_physical_relay();
        if (_failsafe_pub) {
            _failsafe_pub->publish("failsafe/estop",
                                   FailsafeCommandDto(telemetry.device_id(), "ESTOP", result.reason));
        }

        _current_state = domain::InterlockState::ENGAGED;
        GLOBAL_LOG_ERROR("Failsafe Auto E-STOP Triggered! Reason: {}", result.reason);

        throw GlobalExceptionHandler("ERR_EDGE_FAILSAFE_TRIGGERED",
                                     "Critical safety breach: " + result.reason);
    }

    if (result.action == domain::FailsafeAction::BYPASS) {
        GLOBAL_LOG_WARN("Bypass triggered due to warning intrusion. Reason: {}", result.reason);
    }
}

void TriggerFailsafeUseCase::trigger_manual_estop(const std::string& reason) {
    GLOBAL_LOG_DEBUG("Executing TriggerFailsafeUseCase::trigger_manual_estop");

    if (_current_state != domain::InterlockState::RELEASED) {
        GLOBAL_LOG_WARN("Invalid state transition: E-Stop requested but interlock is not RELEASED.");
        throw GlobalExceptionHandler("ERR_COMMON_INVALID_INPUT",
                                     "Engine is already interlocked or in recovery.");
    }

    if (_hw_interlock) _hw_interlock->trigger_physical_relay();
    if (_failsafe_pub) {
        _failsafe_pub->publish("failsafe/estop",
                               FailsafeCommandDto(_edge_device_id, "ESTOP", reason));
    }

    _current_state = domain::InterlockState::ENGAGED;
    GLOBAL_LOG_INFO("Manual E-Stop successfully triggered. State -> ENGAGED (Reason: {})", reason);
}

bool TriggerFailsafeUseCase::execute_recovery_sequence(const std::string& script) {
    GLOBAL_LOG_DEBUG("Executing TriggerFailsafeUseCase::execute_recovery_sequence");

    if (_current_state != domain::InterlockState::ENGAGED) {
        GLOBAL_LOG_WARN("Invalid state transition: Resume requested but engine is not ENGAGED.");
        throw GlobalExceptionHandler("ERR_COMMON_INVALID_INPUT",
                                     "Engine is not in an interlocked state.");
    }

    _current_state = domain::InterlockState::PENDING_RESET_APPROVAL;
    GLOBAL_LOG_INFO("Recovery script received. State -> PENDING_RESET_APPROVAL");

    if (!_recovery || !_recovery->execute_recovery_sequence(script)) {
        GLOBAL_LOG_ERROR("Recovery sequence execution failed!");
        _current_state = domain::InterlockState::ENGAGED;
        return false;
    }

    _current_state = domain::InterlockState::RELEASED;
    if (_failsafe_pub) {
        _failsafe_pub->publish("failsafe/resume",
                               FailsafeCommandDto(_edge_device_id, "RESUME", "RECOVERY_SUCCESS"));
    }

    GLOBAL_LOG_INFO("Recovery successful. State -> RELEASED");
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
