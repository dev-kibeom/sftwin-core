#pragma once

#include <string>

namespace sftwin::edge_control::anomaly_failsafe::application {

struct ResetInterlockRequestDto {
    bool is_field_inspected;
    bool is_manager_approved;
    std::string device_id{"EDGE_NODE_001"};
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
