#include "estop_reset_policy.hpp"

#include <stdexcept>

namespace sftwin::edge_control::anomaly_failsafe::domain {

void EstopResetPolicy::validate_reset_request(InterlockState current_state,
                                              bool is_field_inspected,
                                              bool is_manager_approved) const {
    if (current_state != InterlockState::ENGAGED) {
        throw std::logic_error(
            "Cannot reset E-Stop when interlock state is not ENGAGED.");
    }

    if (!is_field_inspected || !is_manager_approved) {
        throw std::invalid_argument(
            "E-Stop reset rejected. Both field inspection and manager approval are required.");
    }

}

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
