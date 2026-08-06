#include "trigger_failsafe_usecase.hpp"

#include <iostream>

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

TriggerFailsafeUseCase::TriggerFailsafeUseCase(
    std::shared_ptr<ports::IHardwareInterlock> hw_interlock,
    std::shared_ptr<ports::IFailsafePublisher> dds_pub, const domain::FailsafeRule& rule)
    : _hw_interlock(std::move(hw_interlock)), _dds_pub(std::move(dds_pub)), _controller(rule) {}

void TriggerFailsafeUseCase::evaluate_and_trigger(
    const sftwin::edge_control::dtos::TelemetryPacketDto& telemetry) {
    // 1. 도메인 규칙 엔진 평가
    auto result = _controller.check_violations(telemetry);

    // 2. 평가 결과에 따른 분기 (Action Dispatch)
    if (result.action == domain::FailsafeActionEnum::ESTOP) {
        // 하드웨어 차단 (최대 50ms 이내 보장 목표)
        _hw_interlock->trigger_physical_relay();

        // DDS 하향 전송
        dtos::FailsafeCommandDto cmd(telemetry.device_id(), "ESTOP", result.reason,
                                     telemetry.timestamp_ns());
        _dds_pub->publish("failsafe/estop", cmd);

        // GTS 로깅 규약
        std::cerr << "[ERROR] Failsafe E-STOP Triggered! Reason: " << result.reason << std::endl;

        throw common::exceptions::EdgeSystemException("ERR_EDGE_FAILSAFE_TRIGGERED",
                                                      "Critical safety breach: " + result.reason);
    } else if (result.action == domain::FailsafeActionEnum::BYPASS) {
        // 우회 로직 트리거 (Warning 로그 발생)
        std::cout << "[WARN] Bypass triggered due to warning intrusion. Reason: " << result.reason
                  << std::endl;
        return;
    }

    // 정상 상태 모니터링 유지
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application