#pragma once

#include <string>

namespace sftwin::edge_control::realtime_telemetry::application {

struct ProcessTelemetryRequestDto {
    std::string device_id;
};

}  // namespace sftwin::edge_control::realtime_telemetry::application
