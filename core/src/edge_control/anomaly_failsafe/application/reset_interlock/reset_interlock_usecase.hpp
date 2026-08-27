#pragma once

#include <memory>
#include <string>

#include "reset_interlock_dto.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/estop_reset_policy.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_manager.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_state_enum.hpp"
#include "edge_control/contracts/ports/outbound/i_failsafe_publisher.hpp"
#include "edge_control/contracts/ports/outbound/i_hardware_interlock.hpp"
#include "shared/logger/global_system_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class ResetInterlockUseCase {
   public:
    ResetInterlockUseCase(
        std::shared_ptr<domain::InterlockManager> interlock_mgr,
        domain::EstopResetPolicy policy,
        std::shared_ptr<IHardwareInterlock> hw_interlock,
        std::shared_ptr<IFailsafePublisher> failsafe_pub,
        std::shared_ptr<shared::GlobalSystemLogger> system_logger = nullptr);

    [[nodiscard]] domain::InterlockState execute(const ResetInterlockRequestDto& request_dto);

   private:
    std::shared_ptr<domain::InterlockManager> _interlock_mgr;
    domain::EstopResetPolicy _policy;
    std::shared_ptr<IHardwareInterlock> _hw_interlock;
    std::shared_ptr<IFailsafePublisher> _failsafe_pub;
    std::shared_ptr<shared::GlobalSystemLogger> _system_logger;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
