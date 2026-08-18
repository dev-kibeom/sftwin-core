#include "process_telemetry_usecase.hpp"

#include <utility>

#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/utils/time_provider.hpp"
#include "edge_control/realtime_telemetry/domain/telemetry_stream.hpp"

namespace sftwin::edge_control::realtime_telemetry::application {
using namespace sftwin::shared;

ProcessTelemetryUseCase::ProcessTelemetryUseCase(
    std::shared_ptr<ITelemetrySubscriber> telemetry_subscriber,
    std::shared_ptr<IVisionDetector> vision_detector)
    : _telemetry_subscriber(std::move(telemetry_subscriber)),
      _vision_detector(std::move(vision_detector)) {}

TelemetryPacketDto ProcessTelemetryUseCase::get_latest_telemetry(const std::string& device_id) {
    if (!_telemetry_subscriber || !_telemetry_subscriber->is_initialized()) {
        throw GlobalExceptionHandler("ERR_EDGE_DDS_INIT_FAIL",
                                  "Telemetry Subscriber is not initialized.");
    }

    auto packet = _telemetry_subscriber->read_latest_packet(device_id);

    const domain::TelemetryStream stream{packet.device_id(), packet.timestamp_ns()};

    if (stream.is_stale(GlobalTimeProvider::get_steady_time_ns())) {
        throw GlobalExceptionHandler("ERR_EDGE_COMM_TIMEOUT",
                                  "Telemetry heartbeat delayed over 100ms for " + device_id);
    }

    if (_vision_detector) {
        const auto detections = _vision_detector->get_latest_detections();
        for (const auto& det : detections) {
            if (det.bbox[2] > 0.0f && det.bbox[2] < 1.5f) {
                packet.set_warning(true);
                break;
            }
        }
    }

    return packet;
}

}  // namespace sftwin::edge_control::realtime_telemetry::application
