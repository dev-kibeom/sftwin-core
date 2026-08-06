#pragma once
#include <memory>
#include <string>

#include "src/edge_control/realtime_telemetry/dtos/telemetry_packet_dto.hpp"
#include "src/edge_control/realtime_telemetry/ports/i_telemetry_subscriber.hpp"
#include "src/edge_control/realtime_telemetry/ports/i_vision_detector.hpp"

namespace sftwin::edge_control::realtime_telemetry::application {

class ProcessTelemetryUseCase {
   public:
    ProcessTelemetryUseCase(std::shared_ptr<ports::ITelemetrySubscriber> dds_sub,
                            std::shared_ptr<ports::IVisionDetector> vision_adapter);

    dtos::TelemetryPacketDto get_latest_telemetry(const std::string& device_id);

   private:
    std::shared_ptr<ports::ITelemetrySubscriber> _dds_sub;
    std::shared_ptr<ports::IVisionDetector> _vision_adapter;

    uint64_t _get_current_time_ns() const;
};

}  // namespace sftwin::edge_control::realtime_telemetry::application