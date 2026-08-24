#pragma once

#include <cstdint>
#include <string>

namespace sftwin::edge_control {

struct VisionDetectionDto {
    std::string label;
    float confidence{0.0f};
    float bbox[4]{0.0f, 0.0f, 0.0f, 0.0f};  // [x, y, distance_or_width, h]
    uint64_t captured_timestamp_ns{0};
};

}  // namespace sftwin::edge_control
