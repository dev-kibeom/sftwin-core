#pragma once

#include "interlock_state_enum.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

class EstopResetPolicy {
   public:
    [[nodiscard]] bool validate_reset_request(InterlockState current_state,
                                              bool is_field_inspected,
                                              bool is_manager_approved) const;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
