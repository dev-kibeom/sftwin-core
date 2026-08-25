#pragma once

#include <cstdint>
#include <string>

namespace sftwin::edge_control::realtime_telemetry::domain {

class TelemetryStream {
   public:
    TelemetryStream(std::string device_id, uint64_t timestamp_ns)
        : _device_id(std::move(device_id)), _timestamp_ns(timestamp_ns) {}

    [[nodiscard]] bool is_stale(uint64_t current_time_ns) const noexcept {
        // 100ms = 100,000,000ns
        constexpr uint64_t TIMEOUT_NS = 100'000'000ULL;
        if (current_time_ns <= _timestamp_ns) {
            return false;
        }
        return (current_time_ns - _timestamp_ns) > TIMEOUT_NS;
    }

   private:
    std::string _device_id;
    uint64_t _timestamp_ns{0};
};

}  // namespace sftwin::edge_control::realtime_telemetry::domain
