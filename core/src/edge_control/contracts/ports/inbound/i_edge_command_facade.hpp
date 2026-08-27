#pragma once

#include <string>
#include <vector>
#include "edge_control/contracts/dtos/telemetry_packet_dto.hpp"
#include "edge_control/contracts/dtos/vision_detection_dto.hpp"
#include "edge_control/contracts/dtos/recovery_execution_result_dto.hpp"

namespace sftwin::edge_control {

class IEdgeCommandFacade {
   public:
    virtual ~IEdgeCommandFacade() = default;

    virtual void evaluate_failsafe(const TelemetryPacketDto& telemetry,
                                   const std::vector<VisionDetectionDto>& vision_detections) = 0; // 신규 추가
    virtual void execute_manual_estop(const std::string& reason) = 0;
    virtual RecoveryExecutionResultDto resume_recovery_sequence(const std::string& sequence_script) = 0;
    virtual bool reset_estop_interlock(bool is_field_inspected, bool is_manager_approved) = 0;
};

}  // namespace sftwin::edge_control
