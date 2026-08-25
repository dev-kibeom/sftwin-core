#pragma once

#include <string>

namespace sftwin::edge_control::anomaly_failsafe::application {

struct ExecuteRecoverySequenceRequestDto {
    std::string sequence_script;
    std::string device_id{"EDGE_NODE_001"};
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
