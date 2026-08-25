#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace sftwin::edge_control::anomaly_failsafe::domain {

struct TelemetrySnapshot {
    std::string device_id;
    uint64_t timestamp_ns{0};
    std::vector<float> joint_torques;
    float closest_object_distance_m{999.0f};
    float anomaly_score{0.0f};
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
