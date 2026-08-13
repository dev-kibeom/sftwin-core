#pragma once

#include <memory>
#include <string>

#include "src/edge_control/ports/inbound/i_edge_query_facade.hpp"

namespace sftwin::edge_control::realtime_telemetry::application {
class ProcessTelemetryUseCase;
}

namespace sftwin::edge_control::facades::inbound {

class EdgeQueryFacade : public ports::inbound::IEdgeQueryFacade {
   public:
    explicit EdgeQueryFacade(
        std::shared_ptr<realtime_telemetry::application::ProcessTelemetryUseCase> telemetry_uc);

    ~EdgeQueryFacade() override = default;

    realtime_telemetry::dtos::TelemetryPacketDto get_telemetry_status(
        const std::string& device_id) override;

   private:
    std::shared_ptr<realtime_telemetry::application::ProcessTelemetryUseCase> _telemetry_uc;
};

}  // namespace sftwin::edge_control::facades::inbound
