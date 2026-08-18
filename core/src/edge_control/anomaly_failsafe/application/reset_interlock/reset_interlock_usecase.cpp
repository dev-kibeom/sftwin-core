#include "reset_interlock_usecase.hpp"

#include <stdexcept>

#include "edge_control/ports/inbound/dtos/failsafe_command_dto.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/logger/global_system_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
using namespace sftwin::shared;

domain::InterlockState ResetInterlockUseCase::execute(domain::InterlockState current_state,
                                                      bool is_field_inspected,
                                                      bool is_manager_approved) {
    GLOBAL_LOG_DEBUG("Executing ResetInterlockUseCase for device: {}", _edge_device_id);

    try {
        _policy.validate_reset_request(current_state, is_field_inspected, is_manager_approved);
    } catch (const std::invalid_argument& e) {
        GLOBAL_LOG_WARN("E-Stop reset validation rejected: {}", e.what());
        throw GlobalExceptionHandler("ERR_COMMON_FORBIDDEN", e.what());
    } catch (const std::logic_error& e) {
        GLOBAL_LOG_WARN("E-Stop reset invalid state transition: {}", e.what());
        throw GlobalExceptionHandler("ERR_COMMON_INVALID_INPUT", e.what());
    }

    if (_failsafe_pub) {
        _failsafe_pub->publish(
            "failsafe/resume",
            FailsafeCommandDto(_edge_device_id, "RESUME", "MANUAL_2STEP_RESET_SUCCESS"));
    }

    GLOBAL_LOG_INFO("E-Stop Interlock successfully released. State -> RELEASED");
    return domain::InterlockState::RELEASED;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
