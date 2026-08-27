#pragma once

#include <cstdint>
#include <cstddef>
#include <vector>

namespace sftwin::plugins::foxglove_bridge {

// 기존 단위 테스트 alignof == 64를 만족하도록 유지
struct alignas(64) FoxgloveBinaryFrameChunk {
    uint32_t channel_id{0};
    uint64_t timestamp_ns{0};
    uint32_t payload_size{0};
    uint8_t payload[65536 - 16]{0};
};

// 대용량 동적 페이로드 전송용 구조체
struct DynamicFrameChunk {
    uint32_t channel_id{0};
    uint64_t timestamp_ns{0};
    std::vector<uint8_t> payload;
};

}  // namespace sftwin::plugins::foxglove_bridge
