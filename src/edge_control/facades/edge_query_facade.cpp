#include "edge_query_facade.hpp"

namespace sftwin::edge_control::facades {

EdgeQueryFacade::EdgeQueryFacade(
    std::shared_ptr<realtime_telemetry::application::ProcessTelemetryUseCase> telemetry_uc)
    : _telemetry_uc(std::move(telemetry_uc)) {}

sftwin::telemetry::TelemetryPacketProto EdgeQueryFacade::get_telemetry_status(
    const std::string& device_id) {
    // 내부 유즈케이스로 하향 위임 (Delegation)
    return _telemetry_uc->get_latest_telemetry(device_id).get_proto();
}

}  // namespace sftwin::edge_control::facades