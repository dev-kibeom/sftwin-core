#include "edge_query_facade.hpp"

#include <utility>

#include "edge_control/realtime_telemetry/application/process_telemetry/process_telemetry_usecase.hpp"

namespace sftwin::edge_control {

using realtime_telemetry::application::ProcessTelemetryUseCase;

EdgeQueryFacade::EdgeQueryFacade(
    std::shared_ptr<ProcessTelemetryUseCase> telemetry_uc)
    : _telemetry_uc(std::move(telemetry_uc)) {}

TelemetryPacketDto EdgeQueryFacade::get_telemetry_status(const std::string& device_id) {
    if (!_telemetry_uc) {
        return {};
    }
    return _telemetry_uc->get_latest_telemetry(device_id);
}

}  // namespace sftwin::edge_control
