#pragma once

#include <cstdint>
#include <string>

namespace sftwin::edge_control {

struct BoundingBox {
    float x{0.0f};
    float y{0.0f};
    float width{0.0f};
    float height{0.0f};
};

struct VisionDetectionDto {
    std::string label;
    float confidence{0.0f};
    float distance_m{999.0f};  // 계측된 장애물 거리 (m)
    BoundingBox bbox{};
    uint64_t captured_timestamp_ns{0};
};

}  // namespace sftwin::edge_control
