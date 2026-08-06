#include "trigger_failsafe_usecase.hpp"

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/logging/edge_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

TriggerFailsafeUseCase::TriggerFailsafeUseCase(
    std::shared_ptr<ports::IHardwareInterlock> hw_interlock,
    std::shared_ptr<ports::IFailsafePublisher> dds_pub,
    std::shared_ptr<ports::IBehaviorTreeEngine> bt_engine,
    std::shared_ptr<adapters::FailsafeProtobufMapper> mapper, const domain::FailsafeRule& rule)
    : _hw_interlock(std::move(hw_interlock)),
      _dds_pub(std::move(dds_pub)),
      _bt_engine(std::move(bt_engine)),
      _mapper(std::move(mapper)),
      _controller(rule),
      _current_state(domain::EdgeEngineState::ACTIVE_MONITORING),
      _edge_device_id("EDGE_NODE_001") {}

void TriggerFailsafeUseCase::evaluate_and_trigger(
    const sftwin::edge_control::realtime_telemetry::dtos::TelemetryPacketDto& telemetry) {
    // 실시간 감지는 ACTIVE_MONITORING 상태에서만 동작 (불필요 연산 방지)
    if (_current_state != domain::EdgeEngineState::ACTIVE_MONITORING) return;

    auto result = _controller.check_violations(telemetry);

    if (result.action == domain::FailsafeActionEnum::ESTOP) {
        _hw_interlock->trigger_physical_relay();
        auto proto_msg = _mapper->to_protobuf(domain::FailsafeActionEnum::ESTOP,
                                              telemetry.device_id(), result.reason);
        _dds_pub->publish("failsafe/estop",
                          dtos::FailsafeCommandDto(telemetry.device_id(), "ESTOP", result.reason,
                                                   proto_msg.issued_timestamp_ns()));

        _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
        EDGE_LOG_ERROR("Failsafe Auto E-STOP Triggered! Reason: {}", result.reason);

        throw common::exceptions::EdgeSystemException("ERR_EDGE_FAILSAFE_TRIGGERED",
                                                      "Critical safety breach: " + result.reason);
    } else if (result.action == domain::FailsafeActionEnum::BYPASS) {
        EDGE_LOG_WARN("Bypass triggered due to warning intrusion. Reason: {}", result.reason);
    }
}

void TriggerFailsafeUseCase::trigger_manual_estop(const std::string& reason) {
    if (_current_state != domain::EdgeEngineState::ACTIVE_MONITORING) {
        EDGE_LOG_WARN(
            "Invalid state transition: E-Stop requested but state is not ACTIVE_MONITORING.");
        throw common::exceptions::EdgeSystemException(
            "ERR_COMMON_INVALID_INPUT", "Engine is already interlocked or in recovery.");
    }

    _hw_interlock->trigger_physical_relay();
    auto proto_msg =
        _mapper->to_protobuf(domain::FailsafeActionEnum::ESTOP, _edge_device_id, reason);
    _dds_pub->publish("failsafe/estop", dtos::FailsafeCommandDto(_edge_device_id, "ESTOP", reason,
                                                                 proto_msg.issued_timestamp_ns()));

    _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
    EDGE_LOG_INFO("Manual E-Stop successfully triggered. State -> INTERLOCK_ENGAGED (Reason: {})",
                  reason);
}

bool TriggerFailsafeUseCase::execute_behavior_tree_recovery(const std::string& script) {
    if (_current_state != domain::EdgeEngineState::INTERLOCK_ENGAGED) {
        EDGE_LOG_WARN("Invalid state transition: Resume requested but engine is not interlocked.");
        throw common::exceptions::EdgeSystemException("ERR_COMMON_INVALID_INPUT",
                                                      "Engine is not in an interlocked state.");
    }

    _current_state = domain::EdgeEngineState::RECOVERY_PENDING;
    EDGE_LOG_INFO("Recovery script received. State -> RECOVERY_PENDING");

    bool bt_success = _bt_engine->execute_script(script);
    if (!bt_success) {
        EDGE_LOG_ERROR("Behavior Tree script execution failed!");
        _current_state = domain::EdgeEngineState::INTERLOCK_ENGAGED;
        return false;
    }

    _current_state = domain::EdgeEngineState::ACTIVE_MONITORING;
    auto proto_msg = _mapper->to_protobuf(domain::FailsafeActionEnum::RESUME, _edge_device_id,
                                          "BT_RECOVERY_SUCCESS");
    _dds_pub->publish("failsafe/resume",
                      dtos::FailsafeCommandDto(_edge_device_id, "RESUME", "BT_RECOVERY_SUCCESS",
                                               proto_msg.issued_timestamp_ns()));

    EDGE_LOG_INFO("Recovery successful. State -> ACTIVE_MONITORING");
    return true;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application