#pragma once

#include <string>

#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"

namespace sftwin::edge_control {

class ITelemetrySubscriber {
   public:
    virtual ~ITelemetrySubscriber() = default;

    [[nodiscard]] virtual bool is_initialized() const = 0;
    virtual TelemetryPacketDto read_latest_packet(const std::string& device_id) = 0;
};

}  // namespace sftwin::edge_control
