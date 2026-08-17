#pragma once

#include <string>

#include "edge_control/ports/inbound/dtos/telemetry_packet_dto.hpp"

namespace sftwin::edge_control {

class IEdgeQueryFacade {
   public:
    virtual ~IEdgeQueryFacade() = default;

    virtual TelemetryPacketDto get_telemetry_status(const std::string& device_id) = 0;
};

}  // namespace sftwin::edge_control
