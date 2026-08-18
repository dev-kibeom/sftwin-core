#include "edge_command_facade.hpp"

#include <utility>

#include "edge_control/anomaly_failsafe/application/reset_interlock/reset_interlock_usecase.hpp"
#include "edge_control/anomaly_failsafe/application/trigger_failsafe/trigger_failsafe_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_state_enum.hpp"

namespace sftwin::edge_control {

using anomaly_failsafe::application::ResetInterlockUseCase;
using anomaly_failsafe::application::TriggerFailsafeUseCase;
using anomaly_failsafe::domain::InterlockState;

EdgeCommandFacade::EdgeCommandFacade(
    std::shared_ptr<TriggerFailsafeUseCase> failsafe_uc,
    std::shared_ptr<ResetInterlockUseCase> reset_uc)
    : _failsafe_uc(std::move(failsafe_uc)),
      _reset_uc(std::move(reset_uc)) {}

void EdgeCommandFacade::execute_failsafe_estop(const char* reason) {
    if (_failsafe_uc) {
        _failsafe_uc->trigger_manual_estop(reason ? reason : "UNKNOWN_REASON");
    }
}

bool EdgeCommandFacade::resume_process(const std::string& sequence_script) {
    if (!_failsafe_uc) return false;
    return _failsafe_uc->execute_recovery_sequence(sequence_script);
}

bool EdgeCommandFacade::reset_estop_2step(bool is_field_inspected, bool is_manager_approved) {
    if (!_reset_uc || !_failsafe_uc) return false;

    const InterlockState current_state = _failsafe_uc->get_current_state();
    const auto new_state = _reset_uc->execute(
        current_state,
        is_field_inspected,
        is_manager_approved
    );

    return (new_state == InterlockState::RELEASED);
}

}  // namespace sftwin::edge_control
