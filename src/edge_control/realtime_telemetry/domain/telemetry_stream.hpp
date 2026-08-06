#pragma once
#include <cstdint>
#include <string>
#include <vector>

namespace sftwin::edge_control::realtime_telemetry::domain {

class TelemetryStream {
   public:
    std::string device_id;
    uint64_t timestamp_ns;
    std::vector<float> joint_positions;
    std::vector<float> joint_torques;

    // 100ms 이내 상태 갱신 여부 판단 (TIS 제약 조건)
    [[nodiscard]] bool is_stale(uint64_t current_time_ns) const {
        constexpr uint64_t THRESHOLD_NS = 100'000'000ULL;  // 100ms in nanoseconds
        if (current_time_ns < timestamp_ns) return false;  // Edge case 방어
        return (current_time_ns - timestamp_ns) > THRESHOLD_NS;
    }
};

}  // namespace sftwin::edge_control::realtime_telemetry::domain