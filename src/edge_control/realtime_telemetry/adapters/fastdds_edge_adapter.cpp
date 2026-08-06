#include <atomic>
#include <iostream>
#include <mutex>
#include <unordered_map>

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/realtime_telemetry/ports/i_telemetry_subscriber.hpp"

// eProsima FastDDS 관련 가상의 네임스페이스 및 헤더 (실제 구현 시 FastDDS API로 대체)
// #include <fastdds/dds/domain/DomainParticipantFactory.hpp>
// #include <fastdds/dds/subscriber/Subscriber.hpp>
// #include <fastdds/dds/subscriber/DataReader.hpp>

namespace sftwin::edge_control::realtime_telemetry::adapters {

/**
 * @brief FastDDS C++ Zero-Copy 어댑터 구현체 (ITelemetrySubscriber 포트 구현)
 * FDS FCN-EDG-001 요구사항에 맞춰 Lock-Free 큐 또는 뮤텍스 최소화 방식을 사용하여
 * 100ms 이내 초저지연 패킷 수신을 보장합니다.
 */
class FastDdsEdgeAdapter : public ports::ITelemetrySubscriber {
   private:
    std::atomic<bool> _is_initialized{false};

    // 설명: 실제 환경에서는 DataReader의 Listener 콜백에서 Lock-Free Queue(예: readerwriterqueue)에
    // 수신된 Proto 객체를 밀어넣고, 여기서는 Queue에서 Pop하여 DTO로 래핑해 반환합니다.
    // 본 코드는 데모/MVP 스펙(GTS 3.6)에 맞춘 인메모리 버퍼 맵핑 모형입니다.
    std::mutex _buffer_mutex;
    std::unordered_map<std::string, sftwin::telemetry::TelemetryPacketProto> _latest_packets;

   public:
    FastDdsEdgeAdapter() {
        // FastDDS DomainParticipant 및 Subscriber 초기화 로직 수행
        // 성공적으로 초기화 되었다고 가정
        _is_initialized.store(true, std::memory_order_release);
    }

    [[nodiscard]] bool is_initialized() const override {
        return _is_initialized.load(std::memory_order_acquire);
    }

    dtos::TelemetryPacketDto read_latest_packet(const std::string& device_id) override {
        std::lock_guard<std::mutex> lock(_buffer_mutex);

        auto it = _latest_packets.find(device_id);
        if (it == _latest_packets.end()) {
            // 아직 수신된 패킷이 없는 경우, 빈 데이터에 0 타임스탬프를 부여하여
            // UseCase의 is_stale() 로직에서 통신 지연(Timeout)으로 안전하게 걸러지도록 유도합니다.
            sftwin::telemetry::TelemetryPacketProto empty_proto;
            empty_proto.set_device_id(device_id);
            empty_proto.set_timestamp_ns(0);
            return dtos::TelemetryPacketDto(empty_proto);
        }

        return dtos::TelemetryPacketDto(it->second);
    }

    // 통신 스레드(Data Reader Listener)에서 호출되는 콜백 메서드 (예시)
    void on_data_available(const sftwin::telemetry::TelemetryPacketProto& new_packet) {
        std::lock_guard<std::mutex> lock(_buffer_mutex);
        _latest_packets[new_packet.device_id()] = new_packet;
    }
};

}  // namespace sftwin::edge_control::realtime_telemetry::adapters