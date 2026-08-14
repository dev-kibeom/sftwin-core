#pragma once
#include <cstdint>
#include <string>

namespace sftwin::edge_control {

/**
 * @brief AI 비전 객체 감지 전용 독립 DTO
 */
struct VisionDetectionDto {
    std::string label;        // "Worker", "AMR", "Obstacle"
    float confidence{0.0f};
    float bbox[4]{0.0f, 0.0f, 0.0f, 0.0f}; // [x, y, w, h]
    uint64_t captured_timestamp_ns{0};
};

}  // namespace sftwin::edge_control
