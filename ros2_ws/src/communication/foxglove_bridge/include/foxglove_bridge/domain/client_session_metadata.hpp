#pragma once

#include <atomic>
#include <cstdint>

namespace sftwin::plugins::foxglove_bridge {

struct alignas(64) ClientSessionMetadata {
    uint64_t client_id{0};
    std::atomic<uint64_t> queued_bytes{0};
    std::atomic<uint32_t> dropped_frames_count{0};
    uint64_t connected_time_ns{0};
    uint64_t last_ack_time_ns{0};
    bool is_throttled{false};
};

}  // namespace sftwin::plugins::foxglove_bridge
