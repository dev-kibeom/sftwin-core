// core/src/edge_control/realtime_telemetry/ports/i_vision_detector.hpp
#pragma once
#include <vector>
#include <string>

#include "src/edge_control/common/dtos/vision_detection_dto.hpp"

namespace sftwin::edge_control::realtime_telemetry {

class IVisionDetector {
   public:
    virtual ~IVisionDetector() = default;

    // POSIX SHM 또는 TensorRT AI 엔진으로부터 비전 감지 결과 수신
    virtual std::vector<VisionDetectionDto> get_latest_detections() = 0;
};

}  // namespace sftwin::edge_control::realtime_telemetry
