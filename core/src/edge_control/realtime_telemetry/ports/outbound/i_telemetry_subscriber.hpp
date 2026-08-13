#pragma once
#include <string>

#include "src/edge_control/common/dtos/telemetry_packet_dto.hpp"

namespace sftwin::edge_control::realtime_telemetry::ports {

class ITelemetrySubscriber {
   public:
    virtual ~ITelemetrySubscriber() = default;

    // FastDDS 초기화 상태 검증
    [[nodiscard]] virtual bool is_initialized() const = 0;

    // Lock-Free 큐를 통한 최신 패킷 수신 (Dto 반환)
    virtual dtos::TelemetryPacketDto read_latest_packet(const std::string& device_id) = 0;
};

}  // namespace sftwin::edge_control::realtime_telemetry::ports
