#pragma once

#include <stdexcept>
#include <string>

#include "enums/edge_engine_state_enum.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

class EstopResetPolicy {
   public:
    bool validate_reset_request(EdgeEngineState current_state, bool is_field_inspected,
                                bool is_manager_approved) const {
        if (current_state != EdgeEngineState::INTERLOCK_ENGAGED) {
            throw std::logic_error("Cannot reset E-Stop when engine state is not INTERLOCK_ENGAGED.");
        }

        if (!is_field_inspected || !is_manager_approved) {
            throw std::invalid_argument(
                "E-Stop reset rejected. Both field inspection and manager approval are required.");
        }

        return true;
    }
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
