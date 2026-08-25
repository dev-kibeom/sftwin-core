#pragma once

#include <vector>
#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"
#include "edge_control/contracts/dtos/vision_detection_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

struct EvaluateTelemetryFailsafeRequestDto {
    TelemetryPacketDto telemetry;
    std::vector<VisionDetectionDto> vision_detections;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
