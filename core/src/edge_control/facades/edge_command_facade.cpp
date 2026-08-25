#include "edge_command_facade.hpp"

#include <utility>
#include <string>

#include "edge_control/anomaly_failsafe/application/evaluate_telemetry_failsafe/evaluate_telemetry_failsafe_usecase.hpp"
#include "edge_control/anomaly_failsafe/application/trigger_manual_estop/trigger_manual_estop_usecase.hpp"
#include "edge_control/anomaly_failsafe/application/execute_recovery_sequence/execute_recovery_sequence_usecase.hpp"
#include "edge_control/anomaly_failsafe/application/reset_interlock/reset_interlock_usecase.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_manager.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_state_enum.hpp"

namespace sftwin::edge_control {

using anomaly_failsafe::application::EvaluateTelemetryFailsafeUseCase;
using anomaly_failsafe::application::TriggerManualEstopUseCase;
using anomaly_failsafe::application::ExecuteRecoverySequenceUseCase;
using anomaly_failsafe::application::ResetInterlockUseCase;
using anomaly_failsafe::application::TriggerManualEstopRequestDto;
using anomaly_failsafe::application::ExecuteRecoverySequenceRequestDto;
using anomaly_failsafe::application::ResetInterlockRequestDto;
using anomaly_failsafe::domain::InterlockManager;
using anomaly_failsafe::domain::InterlockState;

EdgeCommandFacade::EdgeCommandFacade(
    std::shared_ptr<EvaluateTelemetryFailsafeUseCase> evaluate_uc,
    std::shared_ptr<TriggerManualEstopUseCase> manual_estop_uc,
    std::shared_ptr<ExecuteRecoverySequenceUseCase> recovery_uc,
    std::shared_ptr<ResetInterlockUseCase> reset_uc,
    std::shared_ptr<InterlockManager> interlock_mgr)
    : _evaluate_uc(std::move(evaluate_uc)),
      _manual_estop_uc(std::move(manual_estop_uc)),
      _recovery_uc(std::move(recovery_uc)),
      _reset_uc(std::move(reset_uc)),
      _interlock_mgr(std::move(interlock_mgr)) {}

void EdgeCommandFacade::execute_manual_estop(const std::string& reason) {
    if (_manual_estop_uc) {
        _manual_estop_uc->execute(TriggerManualEstopRequestDto{
            reason.empty() ? "UNKNOWN_REASON" : reason
        });
    }
}

RecoveryExecutionResultDto EdgeCommandFacade::resume_recovery_sequence(const std::string& sequence_script) {
    if (!_recovery_uc) {
        return RecoveryExecutionResultDto::failure("Recovery usecase is null.");
    }
    return _recovery_uc->execute(ExecuteRecoverySequenceRequestDto{
        sequence_script
    });
}

bool EdgeCommandFacade::reset_estop_interlock(bool is_field_inspected, bool is_manager_approved) {
    if (!_reset_uc) return false;

    const auto new_state = _reset_uc->execute(ResetInterlockRequestDto{
        is_field_inspected,
        is_manager_approved
    });

    return (new_state == InterlockState::RELEASED);
}

}  // namespace sftwin::edge_control
