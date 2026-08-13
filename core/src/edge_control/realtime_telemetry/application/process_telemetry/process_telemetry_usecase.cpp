#include "process_telemetry_usecase.hpp"

#include "src/edge_control/common/exceptions/edge_system_exception.hpp"
#include "src/edge_control/common/utils/time_provider.hpp"
#include "src/edge_control/realtime_telemetry/domain/telemetry_stream.hpp"
#include "src/edge_control/realtime_telemetry/ports/outbound/i_telemetry_subscriber.hpp"
#include "src/edge_control/realtime_telemetry/ports/outbound/i_vision_detector.hpp"

namespace sftwin::edge_control::realtime_telemetry::application {

ProcessTelemetryUseCase::ProcessTelemetryUseCase(
    std::shared_ptr<ports::ITelemetrySubscriber> telemetry_subscriber,
    std::shared_ptr<ports::IVisionDetector> vision_detector)
    : _telemetry_subscriber(std::move(telemetry_subscriber)),
      _vision_detector(std::move(vision_detector)) {}

dtos::TelemetryPacketDto ProcessTelemetryUseCase::get_latest_telemetry(
    const std::string& device_id) {
    if (!_telemetry_subscriber || !_telemetry_subscriber->is_initialized()) {
        throw common::exceptions::EdgeSystemException("ERR_EDGE_DDS_INIT_FAIL",
                                                      "Telemetry Subscriber is not initialized.");
    }

    const auto packet = _telemetry_subscriber->read_latest_packet(device_id);

    if (_vision_detector) {
        auto detections = _vision_detector->get_latest_detections();
        // TODO: 수집된 detections를 packet에 결합하거나 비즈니스 로직에 반영
    }

    domain::TelemetryStream stream{
        packet.device_id(),
        packet.timestamp_ns()
    };

    if (stream.is_stale(common::utils::TimeProvider::get_steady_time_ns())) {
        throw common::exceptions::EdgeSystemException(
            "ERR_EDGE_COMM_TIMEOUT", "Telemetry heartbeat delayed over 100ms for " + device_id);
    }

    return packet;
}

}  // namespace sftwin::edge_control::realtime_telemetry::application
