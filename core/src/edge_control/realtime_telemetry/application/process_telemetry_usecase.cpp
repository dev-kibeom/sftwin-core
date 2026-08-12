#include "process_telemetry_usecase.hpp"

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/utils/time_provider.hpp"
#include "src/edge_control/realtime_telemetry/domain/telemetry_stream.hpp"

namespace sftwin::edge_control::realtime_telemetry::application {

ProcessTelemetryUseCase::ProcessTelemetryUseCase(
    std::shared_ptr<ports::ITelemetrySubscriber> dds_sub,
    std::shared_ptr<ports::IVisionDetector> vision_adapter)
    : _dds_sub(std::move(dds_sub)), _vision_adapter(std::move(vision_adapter)) {}

dtos::TelemetryPacketDto ProcessTelemetryUseCase::get_latest_telemetry(
    const std::string& device_id) {
    if (!_dds_sub->is_initialized()) {
        throw common::exceptions::EdgeSystemException("ERR_EDGE_DDS_INIT_FAIL",
                                                      "FastDDS Subscriber is not initialized.");
    }

    auto packet = _dds_sub->read_latest_packet(device_id);

    // DTO에서 원본 데이터를 추출하여 도메인 모델 생성
    domain::TelemetryStream stream{
        packet.device_id(), packet.timestamp_ns()
        // 실제 구현 시 joint_positions 등 전체 매핑 수행
    };

    // TimeProvider를 통한 통일된 시간 측정
    if (stream.is_stale(common::utils::TimeProvider::get_steady_time_ns())) {
        throw common::exceptions::EdgeSystemException(
            "ERR_EDGE_COMM_TIMEOUT", "Telemetry heartbeat delayed over 100ms for " + device_id);
    }

    auto detections = _vision_adapter->get_latest_detections();
    if (!detections.empty()) {
        packet.merge_detections(detections);
        packet.set_warning(true);
    }

    return packet;
}

}  // namespace sftwin::edge_control::realtime_telemetry::application
