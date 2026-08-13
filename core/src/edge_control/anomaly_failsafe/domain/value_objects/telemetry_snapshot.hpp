#pragma once

#include <string>
#include <vector>
#include <cstdint>

namespace sftwin::edge_control::anomaly_failsafe::domain {

struct TelemetrySnapshot {
    std::string device_id;
    uint64_t timestamp_ns;
    std::vector<float> joint_torques;
    float closest_object_distance_m;
    float ai_anomaly_score;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
