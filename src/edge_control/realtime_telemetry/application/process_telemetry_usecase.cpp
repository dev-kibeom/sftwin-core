#include "process_telemetry_usecase.hpp"

#include <chrono>

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/realtime_telemetry/domain/telemetry_stream.hpp"

namespace sftwin::edge_control::application {

ProcessTelemetryUseCase::ProcessTelemetryUseCase(
    std::shared_ptr<ports::ITelemetrySubscriber> dds_sub,
    std::shared_ptr<ports::IVisionDetector> vision_adapter)
    : _dds_sub(std::move(dds_sub)), _vision_adapter(std::move(vision_adapter)) {}

dtos::TelemetryPacketDto ProcessTelemetryUseCase::get_latest_telemetry(
    const std::string& device_id) {
    // 1. Guard Clause: FastDDS 인프라 검증
    if (!_dds_sub->is_initialized()) {
        throw common::exceptions::EdgeSystemException("ERR_EDGE_DDS_INIT_FAIL",
                                                      "FastDDS Subscriber is not initialized.");
    }

    // 2. Lock-Free 버퍼 읽기 (DTO 반환)
    auto packet = _dds_sub->read_latest_packet(device_id);

    // 3. 도메인 매핑 및 Stale (Heartbeat) 검증
    domain::TelemetryStream stream{packet.device_id(), packet.timestamp_ns()};
    if (stream.is_stale(_get_current_time_ns())) {
        throw common::exceptions::EdgeSystemException(
            "ERR_EDGE_COMM_TIMEOUT", "Telemetry heartbeat delayed over 100ms for " + device_id);
    }

    // 4. 비전 감지 결과 병합 (I/O 블로킹 std::cout 제거)
    auto detections = _vision_adapter->get_latest_detections();
    if (!detections.empty()) {
        packet.merge_detections(detections);
        packet.set_warning(true);
    }

    return packet;
}

uint64_t ProcessTelemetryUseCase::_get_current_time_ns() const {
    auto now = std::chrono::high_resolution_clock::now().time_since_epoch();
    return std::chrono::duration_cast<std::chrono::nanoseconds>(now).count();
}

}  // namespace sftwin::edge_control::application