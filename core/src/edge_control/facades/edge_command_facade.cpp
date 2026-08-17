#include "edge_command_facade.hpp"

#include <utility>

#include "edge_control/anomaly_failsafe/application/reset_estop_interlock/reset_estop_interlock_usecase.hpp"
#include "edge_control/anomaly_failsafe/application/trigger_failsafe/trigger_failsafe_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/enums/edge_engine_state_enum.hpp"

namespace sftwin::edge_control {

using anomaly_failsafe::application::ResetEstopInterlockUseCase;
using anomaly_failsafe::application::TriggerFailsafeUseCase;
using anomaly_failsafe::domain::EdgeEngineState;

EdgeCommandFacade::EdgeCommandFacade(
    std::shared_ptr<TriggerFailsafeUseCase> failsafe_uc,
    std::shared_ptr<ResetEstopInterlockUseCase> reset_uc)
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
    if (!_reset_uc) return false;

    const auto new_state = _reset_uc->execute(
        EdgeEngineState::INTERLOCK_ENGAGED,
        is_field_inspected,
        is_manager_approved
    );

    return (new_state == EdgeEngineState::ACTIVE_MONITORING);
}

}  // namespace sftwin::edge_control
