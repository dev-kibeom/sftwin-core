#pragma once

#include <cstdint>
#include <cstddef>

namespace sftwin::plugins::foxglove_bridge {

struct alignas(64) FoxgloveBinaryFrameChunk {
    uint32_t channel_id{0};
    uint64_t timestamp_ns{0};
    uint32_t payload_size{0};
    uint8_t payload[65536 - 16]{0};
};

}  // namespace sftwin::plugins::foxglove_bridge
