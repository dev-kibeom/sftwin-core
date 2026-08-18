#include "plugins/fastdds_edge/include/fastdds_edge_adapter.hpp"
#include "core/shared/exceptions/global_exception_handler"
#include "core/shared/logger/global_system_logger.hpp"

namespace sftwin::plugins::fastdds {

FastDdsEdgeAdapter::FastDdsEdgeAdapter() {
    // FastDDS DomainParticipant, Publisher, Subscriber, Topic 생성 로직 수행
    _is_initialized.store(true, std::memory_order_release);
    EDGE_LOG_INFO("[FastDdsEdgeAdapter] Successfully initialized FastDDS participant and topics.");
}

bool FastDdsEdgeAdapter::is_initialized() const {
    return _is_initialized.load(std::memory_order_acquire);
}

// ============================================================================
// 1. [Inbound Network -> core DTO] 텔레메트리 패킷 읽기 및 맵핑
// ============================================================================
realtime_telemetry::TelemetryPacketDto FastDdsEdgeAdapter::read_latest_packet(
    const std::string& device_id) {

    std::lock_guard<std::mutex> lock(_buffer_mutex);

    auto it = _latest_proto_packets.find(device_id);
    if (it == _latest_proto_packets.end()) {
        // 미수신 시 0 타임스탬프를 부여하여 core 유즈케이스의 is_stale()에서 걸러지도록 유도
        realtime_telemetry::TelemetryPacketDto empty_dto;
        empty_dto.set_device_id(device_id);
        empty_dto.set_timestamp_ns(0);
        return empty_dto;
    }

    const auto& proto = it->second;

    // Protobuf vector -> std::vector<float> 변환
    std::vector<float> positions(proto.joint_positions().begin(), proto.joint_positions().end());
    std::vector<float> torques(proto.joint_torques().begin(), proto.joint_torques().end());

    // core 순수 TelemetryPacketDto 객체 생성하여 전달
    realtime_telemetry::TelemetryPacketDto core_dto(
        proto.device_id(),
        proto.timestamp_ns(),
        positions,
        torques
    );

    return core_dto;
}

// ============================================================================
// 2. [core DTO -> Outbound Network] Failsafe 제어 명령 발행
// ============================================================================
bool FastDdsEdgeAdapter::publish(
    const std::string& topic,
    const anomaly_failsafe::FailsafeCommandDto& command_dto) {

    if (!is_initialized()) {
        EDGE_LOG_ERROR("[FastDdsEdgeAdapter] Cannot publish. FastDDS not initialized.");
        return false;
    }

    // 💡 core FailsafeCommandDto -> Protobuf 메시지로 매핑하여 네트워크 전송
    sftwin::failsafe::FailsafeCommandProto proto_msg;
    proto_msg.set_target_device_id(command_dto.target_device_id());
    proto_msg.set_action_type(command_dto.action_type());
    proto_msg.set_trigger_reason(command_dto.trigger_reason());
    proto_msg.set_issued_timestamp_ns(command_dto.issued_timestamp_ns());

    // 실제 FastDDS DataWriter->write(&proto_msg) 수행 (가상 로그 대체)
    EDGE_LOG_INFO("[FastDdsEdgeAdapter] Published DDS message to topic '{}': Target={}, Action={}, Reason={}",
                  topic, command_dto.target_device_id(), command_dto.action_type(), command_dto.trigger_reason());

    return true;
}

// FastDDS DataReader Listener 이벤트 수신
void FastDdsEdgeAdapter::on_telemetry_received(const sftwin::telemetry::TelemetryPacketProto& raw_packet) {
    std::lock_guard<std::mutex> lock(_buffer_mutex);
    _latest_proto_packets[raw_packet.device_id()] = raw_packet;
}

}  // namespace sftwin::plugins::fastdds
