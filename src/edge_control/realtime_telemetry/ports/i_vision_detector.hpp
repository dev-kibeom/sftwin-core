#pragma once
#include <vector>

#include "telemetry_packet.pb.h"

namespace sftwin::edge_control::realtime_telemetry::ports {

class IVisionDetector {
   public:
    virtual ~IVisionDetector() = default;

    // POSIX SHM을 통한 비전 감지 객체 배열 수신
    virtual std::vector<sftwin::telemetry::DetectedObject> get_latest_detections() = 0;
};

}  // namespace sftwin::edge_control::realtime_telemetry::ports