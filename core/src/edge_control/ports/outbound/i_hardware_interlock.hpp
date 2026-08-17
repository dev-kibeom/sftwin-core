#pragma once

#include <string>

#include "edge_control/anomaly_failsafe/domain/enums/interlock_state_enum.hpp"

namespace sftwin::edge_control {

class IHardwareInterlock {
   public:
    virtual ~IHardwareInterlock() = default;

    virtual void trigger_physical_relay() = 0;
    virtual bool release_interlock(const std::string& operator_approval_token) = 0;
    [[nodiscard]] virtual anomaly_failsafe::domain::InterlockState get_state() const = 0;
};

}  // namespace sftwin::edge_control
