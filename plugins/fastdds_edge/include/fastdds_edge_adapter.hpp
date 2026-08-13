#pragma once
#include <atomic>
#include <mutex>
#include <unordered_map>
#include <memory>
#include <string>

// 1. core 아웃바운드 포트 인클루드 (DIP 준수)
#include "core/src/edge_control/realtime_telemetry/ports/outbound/i_telemetry_subscriber.hpp"
#include "core/src/edge_control/anomaly_failsafe/ports/outbound/i_failsafe_publisher.hpp"

// 2. core 순수 DTO
#include "core/src/edge_control/realtime_telemetry/ports/outbound/telemetry_packet_dto.hpp"
#include "core/src/edge_control/anomaly_failsafe/ports/outbound/failsafe_command_dto.hpp"

// 3. 외곽 Protobuf / IDL 스키마 (플러그인 내부에서만 참조!)
#include "telemetry_packet.pb.h"
#include "failsafe_command.pb.h"

namespace sftwin::plugins::fastdds {

using namespace sftwin::edge_control;

/**
 * @brief FastDDS 미들웨어 연동 및 DTO ↔ Protobuf/CDR 변환을 전담하는 Outer Adapter
 */
class FastDdsEdgeAdapter : public realtime_telemetry::ports::ITelemetrySubscriber,
                          public anomaly_failsafe::ports::IFailsafePublisher {
   private:
    std::atomic<bool> _is_initialized{false};
    std::mutex _buffer_mutex;

    // 수신된 텔레메트리 원본 메시지 링버퍼/맵 (Lock-Free 구조로 확장 가능)
    std::unordered_map<std::string, sftwin::telemetry::TelemetryPacketProto> _latest_proto_packets;

   public:
    FastDdsEdgeAdapter();
    ~FastDdsEdgeAdapter() override = default;

    // --- ITelemetrySubscriberPort 구현 ---
    [[nodiscard]] bool is_initialized() const override;
    realtime_telemetry::ports::TelemetryPacketDto read_latest_packet(const std::string& device_id) override;

    // --- IFailsafePublisherPort 구현 ---
    bool publish(const std::string& topic, const anomaly_failsafe::ports::FailsafeCommandDto& command_dto) override;

    // FastDDS DataReader Listener 콜백 (네트워크 패킷 수신 시 호출)
    void on_telemetry_received(const sftwin::telemetry::TelemetryPacketProto& raw_packet);
};

}  // namespace sftwin::plugins::fastdds
