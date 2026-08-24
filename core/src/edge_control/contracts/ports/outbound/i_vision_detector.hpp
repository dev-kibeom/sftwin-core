#pragma once

#include <vector>

#include "edge_control/contracts/dtos/vision_detection_dto.hpp"

namespace sftwin::edge_control {

class IVisionDetector {
   public:
    virtual ~IVisionDetector() = default;

    virtual std::vector<VisionDetectionDto> get_latest_detections() = 0;
};

}  // namespace sftwin::edge_control
