#pragma once
#include <string>
#include "src/edge_control/common/dtos/telemetry_packet_dto.hpp"

namespace sftwin::edge_control::ports::inbound {

class IEdgeQueryFacade {
   public:
    virtual ~IEdgeQueryFacade() = default;

    // Protobuf 클래스 대신 순수 core DTO 반환
    virtual realtime_telemetry::dtos::TelemetryPacketDto get_telemetry_status(
        const std::string& device_id) = 0;
};

}  // namespace sftwin::edge_control::ports::inbound
