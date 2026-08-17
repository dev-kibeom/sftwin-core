#pragma once

#include <memory>
#include <string>
#include <vector>

#include "edge_control/anomaly_failsafe/domain/enums/edge_engine_state_enum.hpp"
#include "edge_control/anomaly_failsafe/domain/failsafe_controller.hpp"
#include "edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "edge_control/ports/inbound/dtos/telemetry_packet_dto.hpp"
#include "edge_control/ports/inbound/dtos/vision_detection_dto.hpp"
#include "edge_control/ports/outbound/i_failsafe_publisher.hpp"
#include "edge_control/ports/outbound/i_hardware_interlock.hpp"
#include "edge_control/ports/outbound/i_recovery_sequence.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class TriggerFailsafeUseCase {
   public:
    TriggerFailsafeUseCase(std::shared_ptr<IHardwareInterlock> hw_interlock,
                           std::shared_ptr<IFailsafePublisher> failsafe_pub,
                           std::shared_ptr<IRecoverySequence> recovery,
                           const domain::FailsafeRule& rule);

    void evaluate_and_trigger(const TelemetryPacketDto& telemetry,
                              const std::vector<VisionDetectionDto>& vision_detections);

    void trigger_manual_estop(const std::string& reason);

    [[nodiscard]] bool execute_recovery_sequence(const std::string& script);

    [[nodiscard]] domain::EdgeEngineState get_current_state() const noexcept {
        return _current_state;
    }

   private:
    [[nodiscard]] float _extract_min_distance(
        const std::vector<VisionDetectionDto>& detections) const noexcept;

    std::shared_ptr<IHardwareInterlock> _hw_interlock;
    std::shared_ptr<IFailsafePublisher> _failsafe_pub;
    std::shared_ptr<IRecoverySequence> _recovery;

    domain::FailsafeController _controller;
    domain::EdgeEngineState _current_state{domain::EdgeEngineState::ACTIVE_MONITORING};
    std::string _edge_device_id{"EDGE_NODE_001"};
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
