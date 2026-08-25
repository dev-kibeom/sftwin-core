#pragma once

#include <string>
#include <vector>

#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"
#include "edge_control/contracts/dtos/webrtc_stream_dto.hpp"

namespace sftwin::edge_control {

class IEdgeQueryFacade {
   public:
    virtual ~IEdgeQueryFacade() = default;

    virtual TelemetryPacketDto get_telemetry_status(const std::string& device_id) = 0;
    virtual WebRtcSessionDto get_webrtc_stream_session(const std::string& device_id) = 0;
    virtual DeviceStreamSummaryDto list_active_scada_streams() = 0;
};

}  // namespace sftwin::edge_control
