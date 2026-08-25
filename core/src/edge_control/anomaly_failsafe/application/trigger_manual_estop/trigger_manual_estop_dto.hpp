#pragma once

#include <string>

namespace sftwin::edge_control::anomaly_failsafe::application {

struct TriggerManualEstopRequestDto {
    std::string reason;
    std::string device_id{"EDGE_NODE_001"};
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
