#include "reset_estop_interlock_usecase.hpp"

#include <stdexcept>

#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/logger/global_system_logger.hpp"
#include "edge_control/ports/inbound/dtos/failsafe_command_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
using namespace sftwin::shared;

domain::EdgeEngineState ResetEstopInterlockUseCase::execute(domain::EdgeEngineState current_state,
                                                             bool is_field_inspected,
                                                             bool is_manager_approved) {
    GLOBAL_LOG_INFO("E-Stop 2-Step Reset requested for device: {}", _edge_device_id);

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

    GLOBAL_LOG_INFO("E-Stop Interlock successfully released. State -> ACTIVE_MONITORING");
    return domain::EdgeEngineState::ACTIVE_MONITORING;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
