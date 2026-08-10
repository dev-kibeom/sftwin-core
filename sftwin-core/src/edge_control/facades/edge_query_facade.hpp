#pragma once
#include <memory>
#include <string>

#include "src/edge_control/realtime_telemetry/application/process_telemetry_usecase.hpp"
#include "telemetry_packet.pb.h"

namespace sftwin::edge_control::facades {

class EdgeQueryFacade {
   private:
    std::shared_ptr<realtime_telemetry::application::ProcessTelemetryUseCase> _telemetry_uc;

   public:
    explicit EdgeQueryFacade(
        std::shared_ptr<realtime_telemetry::application::ProcessTelemetryUseCase> telemetry_uc);

    sftwin::telemetry::TelemetryPacketProto get_telemetry_status(const std::string& device_id);
};

}  // namespace sftwin::edge_control::facades
