#include "process_telemetry_usecase.hpp"

#include <utility>

#include "edge_control/realtime_telemetry/domain/telemetry_stream.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/utils/time_provider.hpp"

namespace sftwin::edge_control::realtime_telemetry::application {
using namespace sftwin::shared;

ProcessTelemetryUseCase::ProcessTelemetryUseCase(
    std::shared_ptr<ITelemetrySubscriber> telemetry_subscriber,
    std::shared_ptr<IVisionDetector> vision_detector,
    std::shared_ptr<GlobalSystemLogger> system_logger)
    : _telemetry_subscriber(std::move(telemetry_subscriber)),
      _vision_detector(std::move(vision_detector)),
      _system_logger(system_logger ? std::move(system_logger)
                                   : std::make_shared<GlobalSystemLogger>("ProcessTelemetryUseCase")) {}

TelemetryPacketDto ProcessTelemetryUseCase::execute(const ProcessTelemetryRequestDto& request_dto) {
    _system_logger->debug("Executing ProcessTelemetryUseCase for device: {}", request_dto.device_id);

    // 1. 구독자 포트 가용성 검증
    if (!_telemetry_subscriber || !_telemetry_subscriber->is_initialized()) {
        _system_logger->error("Telemetry Subscriber is not initialized.");
        throw GlobalExceptionHandler(
            GlobalErrorCode::ERR_EDGE_DDS_INIT_FAIL,
            "Telemetry Subscriber is not initialized."
        );
    }

    // 2. 최신 텔레메트리 패킷 조회
    auto packet = _telemetry_subscriber->read_latest_packet(request_dto.device_id);

    // 3. 통신 지연(Heartbeat Timeout > 100ms) 도메인 검증
    const domain::TelemetryStream stream{packet.device_id(), packet.timestamp_ns()};
    if (stream.is_stale(GlobalTimeProvider::get_steady_time_ns())) {
        _system_logger->warn("Telemetry heartbeat delayed over 100ms for device: {}", request_dto.device_id);
        throw GlobalExceptionHandler(
            GlobalErrorCode::ERR_EDGE_COMM_TIMEOUT,
            "Telemetry heartbeat delayed over 100ms for " + request_dto.device_id
        );
    }

    // 4. 비전 감지 결과 기반 경고 플래그 갱신
    if (_vision_detector) {
        const auto detections = _vision_detector->get_latest_detections();
        for (const auto& det : detections) {
            // 명시적 distance_m 필드 검사 (주의 반경 1.5m 이내)
            if (det.distance_m > 0.0f && det.distance_m < 1.5f) {
                packet.set_warning(true);
                _system_logger->debug("Object detected within warning distance ({}m) for device: {}",
                                 det.distance_m, request_dto.device_id);
                break;
            }
        }
    }

    return packet;
}

}  // namespace sftwin::edge_control::realtime_telemetry::application
