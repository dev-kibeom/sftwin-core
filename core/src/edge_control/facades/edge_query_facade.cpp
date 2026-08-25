#include "edge_query_facade.hpp"

#include <algorithm>
#include <utility>
#include <vector>

#include "edge_control/realtime_telemetry/application/process_telemetry/process_telemetry_dto.hpp"
#include "edge_control/realtime_telemetry/application/process_telemetry/process_telemetry_usecase.hpp"
#include "shared/utils/time_provider.hpp"

namespace sftwin::edge_control {

using realtime_telemetry::application::ProcessTelemetryUseCase;
using realtime_telemetry::application::ProcessTelemetryRequestDto;
using shared::GlobalTimeProvider;

EdgeQueryFacade::EdgeQueryFacade(
    std::shared_ptr<ProcessTelemetryUseCase> telemetry_uc,
    std::string signaling_base_url)
    : _telemetry_uc(std::move(telemetry_uc)),
      _signaling_base_url(std::move(signaling_base_url)) {}

TelemetryPacketDto EdgeQueryFacade::get_telemetry_status(const std::string& device_id) {
    if (!_telemetry_uc) {
        return {};
    }
    return _telemetry_uc->execute(ProcessTelemetryRequestDto{device_id});
}

WebRtcSessionDto EdgeQueryFacade::get_webrtc_stream_session(const std::string& device_id) {
    std::string stream_type = "ROBOT_POV";
    if (device_id.find("AMR") != std::string::npos || device_id.find("amr") != std::string::npos) {
        stream_type = "AMR_TOP_DOWN";
    } else if (device_id.find("CCTV") != std::string::npos) {
        stream_type = "CCTV_CELL";
    }

    const std::string signaling_url = _signaling_base_url + "/" + device_id;
    const std::string session_id = "WSS-" + device_id;
    const uint64_t now_ns = GlobalTimeProvider::get_steady_time_ns();

    return WebRtcSessionDto(device_id, stream_type, signaling_url, session_id, true, now_ns);
}

DeviceStreamSummaryDto EdgeQueryFacade::list_active_scada_streams() {
    const std::vector<std::string> default_devices = {
        "ROBOT_ARM_01",
        "AMR_NAV2_01",
        "CCTV_MAIN_CELL"
    };

    std::vector<WebRtcSessionDto> streams;
    streams.reserve(default_devices.size());

    for (const auto& dev_id : default_devices) {
        streams.push_back(get_webrtc_stream_session(dev_id));
    }

    return DeviceStreamSummaryDto(std::move(streams));
}

}  // namespace sftwin::edge_control
