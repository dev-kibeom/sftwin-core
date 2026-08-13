#include "edge_query_facade.hpp"

#include "src/edge_control/realtime_telemetry/application/process_telemetry/process_telemetry_usecase.hpp"

namespace sftwin::edge_control::facades::inbound {

using realtime_telemetry::application::ProcessTelemetryUseCase;
using realtime_telemetry::dtos::TelemetryPacketDto;

EdgeQueryFacade::EdgeQueryFacade(
    std::shared_ptr<ProcessTelemetryUseCase> telemetry_uc)
    : _telemetry_uc(std::move(telemetry_uc)) {}

TelemetryPacketDto EdgeQueryFacade::get_telemetry_status(const std::string& device_id) {
    if (!_telemetry_uc) {
        return {}; // Null 지점 방어
    }

    // core DTO를 그대로 하향 위임하여 반환
    return _telemetry_uc->get_latest_telemetry(device_id);
}

}  // namespace sftwin::edge_control::facades::inbound
