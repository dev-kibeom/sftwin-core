#pragma once

#include <memory>
#include <string>

#include "process_telemetry_dto.hpp"
#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"
#include "edge_control/contracts/ports/outbound/i_telemetry_subscriber.hpp"
#include "edge_control/contracts/ports/outbound/i_vision_detector.hpp"
#include "shared/logger/global_system_logger.hpp"

namespace sftwin::edge_control::realtime_telemetry::application {

class ProcessTelemetryUseCase {
   public:
    ProcessTelemetryUseCase(
        std::shared_ptr<ITelemetrySubscriber> telemetry_subscriber,
        std::shared_ptr<IVisionDetector> vision_detector,
        std::shared_ptr<shared::GlobalSystemLogger> system_logger = nullptr);

    TelemetryPacketDto execute(const ProcessTelemetryRequestDto& request_dto);

   private:
    std::shared_ptr<ITelemetrySubscriber> _telemetry_subscriber;
    std::shared_ptr<IVisionDetector> _vision_detector;
    std::shared_ptr<shared::GlobalSystemLogger> _system_logger;
};

}  // namespace sftwin::edge_control::realtime_telemetry::application
