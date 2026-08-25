#pragma once

#include <memory>
#include <string>

#include "trigger_manual_estop_dto.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_manager.hpp"
#include "edge_control/contracts/ports/outbound/i_failsafe_publisher.hpp"
#include "edge_control/contracts/ports/outbound/i_hardware_interlock.hpp"
#include "shared/logger/global_system_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class TriggerManualEstopUseCase {
   public:
    TriggerManualEstopUseCase(
        std::shared_ptr<domain::InterlockManager> interlock_mgr,
        std::shared_ptr<IHardwareInterlock> hw_interlock,
        std::shared_ptr<IFailsafePublisher> failsafe_pub,
        std::shared_ptr<shared::GlobalSystemLogger> system_logger = nullptr);

    void execute(const TriggerManualEstopRequestDto& request_dto);

   private:
    std::shared_ptr<domain::InterlockManager> _interlock_mgr;
    std::shared_ptr<IHardwareInterlock> _hw_interlock;
    std::shared_ptr<IFailsafePublisher> _failsafe_pub;
    std::shared_ptr<shared::GlobalSystemLogger> _system_logger;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
