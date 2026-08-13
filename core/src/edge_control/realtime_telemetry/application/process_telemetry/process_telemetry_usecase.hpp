#pragma once

#include <memory>
#include <string>

#include "src/edge_control/common/dtos/telemetry_packet_dto.hpp"

namespace sftwin::edge_control::realtime_telemetry::ports {
class ITelemetrySubscriber;
class IVisionDetector;
}

namespace sftwin::edge_control::realtime_telemetry::application {

class ProcessTelemetryUseCase {
   public:
    ProcessTelemetryUseCase(
        std::shared_ptr<ports::ITelemetrySubscriber> telemetry_subscriber,
        std::shared_ptr<ports::IVisionDetector> vision_detector);

    dtos::TelemetryPacketDto get_latest_telemetry(const std::string& device_id);

   private:
    std::shared_ptr<ports::ITelemetrySubscriber> _telemetry_subscriber;
    std::shared_ptr<ports::IVisionDetector> _vision_detector;
};

}  // namespace sftwin::edge_control::realtime_telemetry::application
