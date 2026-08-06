#pragma once
#include <memory>

#include "src/edge_control/anomaly_failsafe/domain/failsafe_controller.hpp"
#include "src/edge_control/anomaly_failsafe/ports/i_failsafe_publisher.hpp"
#include "src/edge_control/anomaly_failsafe/ports/i_hardware_interlock.hpp"
#include "src/edge_control/realtime_telemetry/dtos/telemetry_packet_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class TriggerFailsafeUseCase {
   private:
    std::shared_ptr<ports::IHardwareInterlock> _hw_interlock;
    std::shared_ptr<ports::IFailsafePublisher> _dds_pub;
    domain::FailsafeController _controller;

   public:
    TriggerFailsafeUseCase(std::shared_ptr<ports::IHardwareInterlock> hw_interlock,
                           std::shared_ptr<ports::IFailsafePublisher> dds_pub,
                           const domain::FailsafeRule& rule);

    void evaluate_and_trigger(const sftwin::edge_control::dtos::TelemetryPacketDto& telemetry);
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application