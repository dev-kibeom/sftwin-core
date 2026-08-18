#pragma once

#include <string>
#include "core/shared/dtos/telemetry_packet_dto.hpp"
#include "telemetry_packet.pb.h"

namespace sftwin::plugins::protobuf_codec {

class TelemetryProtobufMapper {
   public:
    // 1. Protobuf Proto -> core TelemetryPacketDto 변환
    static sftwin::edge_control::TelemetryPacketDto to_core_dto(
        const sftwin::telemetry::TelemetryPacketProto& proto);

    // 2. core TelemetryPacketDto -> Protobuf Proto 변환 (상위 Pybind / 네트워크 송신용)
    static sftwin::telemetry::TelemetryPacketProto to_protobuf(
        const sftwin::edge_control::TelemetryPacketDto& dto);
};

}  // namespace sftwin::plugins::protobuf_codec
