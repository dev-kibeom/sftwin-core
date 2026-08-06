#pragma once
#include <cstdint>
#include <string>
#include <vector>

#include "telemetry_packet.pb.h"

namespace sftwin::edge_control::realtime_telemetry::dtos {
/**
 * @brief 실시간 텔레메트리 패킷 전송을 위한 래퍼 DTO
 * 내부적으로 Protobuf 메세지를 캡슐화하여 비즈니스 로직에서의 직접적인 조작을 방지합니다.
 */
class TelemetryPacketDto {
   private:
    sftwin::telemetry::TelemetryPacketProto _proto_data;

   public:
    TelemetryPacketDto() = default;

    explicit TelemetryPacketDto(const sftwin::telemetry::TelemetryPacketProto& proto)
        : _proto_data(proto) {}

    [[nodiscard]] std::string device_id() const { return _proto_data.device_id(); }

    [[nodiscard]] uint64_t timestamp_ns() const { return _proto_data.timestamp_ns(); }

    // 비전 감지 결과 병합 (Tell-Don't-Ask 원칙 적용)
    void merge_detections(const std::vector<sftwin::telemetry::DetectedObject>& detections) {
        for (const auto& det : detections) {
            auto* new_det = _proto_data.add_detected_objects();
            new_det->CopyFrom(det);
        }
    }

    // 이상 상태 포착 시 플래그 갱신
    void set_warning(bool is_warning) { _proto_data.set_is_warning(is_warning); }

    // 외곽 계층(Facade 등) 반환을 위한 원본 Proto 접근자
    [[nodiscard]] const sftwin::telemetry::TelemetryPacketProto& get_proto() const {
        return _proto_data;
    }
};

}  // namespace sftwin::edge_control::realtime_telemetry::dtos