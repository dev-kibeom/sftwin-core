#pragma once

#include <memory>
#include <vector>

#include "evaluate_telemetry_failsafe_dto.hpp"
#include "edge_control/anomaly_failsafe/domain/failsafe_evaluation/failsafe_evaluator.hpp"
#include "edge_control/anomaly_failsafe/domain/failsafe_evaluation/failsafe_rule.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_manager.hpp"
#include "edge_control/contracts/ports/outbound/i_failsafe_publisher.hpp"
#include "edge_control/contracts/ports/outbound/i_hardware_interlock.hpp"
#include "shared/logger/global_system_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class EvaluateTelemetryFailsafeUseCase {
   public:
    EvaluateTelemetryFailsafeUseCase(
        std::shared_ptr<domain::InterlockManager> interlock_mgr,
        std::shared_ptr<IHardwareInterlock> hw_interlock,
        std::shared_ptr<IFailsafePublisher> failsafe_pub,
        const domain::FailsafeRule& rule,
        std::shared_ptr<shared::GlobalSystemLogger> system_logger = nullptr);

    void execute(const EvaluateTelemetryFailsafeRequestDto& request_dto);

   private:
    [[nodiscard]] float _extract_min_distance(
        const std::vector<VisionDetectionDto>& detections) const noexcept;

    std::shared_ptr<domain::InterlockManager> _interlock_mgr;
    std::shared_ptr<IHardwareInterlock> _hw_interlock;
    std::shared_ptr<IFailsafePublisher> _failsafe_pub;
    domain::FailsafeEvaluator _evaluator;
    std::shared_ptr<shared::GlobalSystemLogger> _system_logger;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
