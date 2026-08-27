#pragma once

#include <memory>
#include <string>

#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"
#include "edge_control/contracts/dtos/webrtc_session_dto.hpp"
#include "edge_control/contracts/ports/inbound/i_edge_query_facade.hpp"

namespace sftwin::edge_control::realtime_telemetry::application {
class ProcessTelemetryUseCase;
}

namespace sftwin::edge_control {

class EdgeQueryFacade : public IEdgeQueryFacade {
   public:
    explicit EdgeQueryFacade(
        std::shared_ptr<realtime_telemetry::application::ProcessTelemetryUseCase> telemetry_uc,
        std::string signaling_base_url = "ws://localhost:8080/webrtc");

    ~EdgeQueryFacade() override = default;

    TelemetryPacketDto get_telemetry_status(const std::string& device_id) override;
    WebRtcSessionDto get_webrtc_stream_session(const std::string& device_id) override;
    DeviceStreamSummaryDto list_active_scada_streams() override;

   private:
    std::shared_ptr<realtime_telemetry::application::ProcessTelemetryUseCase> _telemetry_uc;
    std::string _signaling_base_url;
};

}  // namespace sftwin::edge_control
