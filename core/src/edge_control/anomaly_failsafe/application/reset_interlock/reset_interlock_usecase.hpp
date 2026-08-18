#pragma once

#include <memory>
#include <string>
#include <utility>

#include "edge_control/anomaly_failsafe/domain/interlock_management/estop_reset_policy.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_state_enum.hpp"
#include "edge_control/ports/outbound/i_failsafe_publisher.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class ResetInterlockUseCase {
   public:
    ResetInterlockUseCase(std::string device_id,
                          domain::EstopResetPolicy policy,
                          std::shared_ptr<IFailsafePublisher> failsafe_pub)
        : _edge_device_id(std::move(device_id)),
          _policy(std::move(policy)),
          _failsafe_pub(std::move(failsafe_pub)) {}

    [[nodiscard]] domain::InterlockState execute(domain::InterlockState current_state,
                                                 bool is_field_inspected,
                                                 bool is_manager_approved);

   private:
    std::string _edge_device_id;
    domain::EstopResetPolicy _policy;
    std::shared_ptr<IFailsafePublisher> _failsafe_pub;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
