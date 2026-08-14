#pragma once

#include <memory>
#include <string>
#include <vector>

#include "src/edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "src/edge_control/anomaly_failsafe/domain/edge_local_enums.hpp"
#include "src/edge_control/anomaly_failsafe/domain/failsafe_controller.hpp"
#include "src/edge_control/anomaly_failsafe/ports/outbound/i_failsafe_publisher.hpp"
#include "src/edge_control/anomaly_failsafe/ports/outbound/i_hardware_interlock.hpp"
#include "src/edge_control/anomaly_failsafe/ports/outbound/i_recovery_sequence.hpp"
#include "src/edge_control/common/dtos/telemetry_packet_dto.hpp"
#include "src/edge_control/common/dtos/vision_detection_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class TriggerFailsafeUseCase {
   public:
    TriggerFailsafeUseCase(std::shared_ptr<IHardwareInterlock> hw_interlock,
                           std::shared_ptr<IFailsafePublisher> failsafe_pub,
                           std::shared_ptr<IRecoverySequence> recovery,
                           const domain::FailsafeRule& rule);

    // 실시간 텔레메트리 기반 이상 감지 (100ms Loop)
    void evaluate_and_trigger(
        const TelemetryPacketDto& telemetry,
        const std::vector<VisionDetectionDto>& vision_detections
    );

    // 수동 제어 및 복구
    void trigger_manual_estop(const std::string& reason);

    [[nodiscard]] bool execute_recovery_sequence(const std::string& script);

    // 상태 조회
    [[nodiscard]] domain::EdgeEngineState get_current_state() const noexcept {
        return _current_state;
    }

   private:
    std::shared_ptr<IHardwareInterlock> _hw_interlock;
    std::shared_ptr<IFailsafePublisher> _failsafe_pub;
    std::shared_ptr<IRecoverySequence> _recovery;

    domain::FailsafeController _controller;
    domain::EdgeEngineState _current_state;
    std::string _edge_device_id;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
