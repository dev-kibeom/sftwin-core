#pragma once

#include <memory>
#include <string>

#include "edge_control/contracts/dtos/recovery_execution_result_dto.hpp"
#include "edge_control/contracts/ports/inbound/i_edge_command_facade.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
class EvaluateTelemetryFailsafeUseCase;
class TriggerManualEstopUseCase;
class ExecuteRecoverySequenceUseCase;
class ResetInterlockUseCase;
}

namespace sftwin::edge_control::anomaly_failsafe::domain {
class InterlockManager;
}

namespace sftwin::edge_control {

class EdgeCommandFacade : public IEdgeCommandFacade {
   public:
    explicit EdgeCommandFacade(
        std::shared_ptr<anomaly_failsafe::application::EvaluateTelemetryFailsafeUseCase> evaluate_uc,
        std::shared_ptr<anomaly_failsafe::application::TriggerManualEstopUseCase> manual_estop_uc,
        std::shared_ptr<anomaly_failsafe::application::ExecuteRecoverySequenceUseCase> recovery_uc,
        std::shared_ptr<anomaly_failsafe::application::ResetInterlockUseCase> reset_uc,
        std::shared_ptr<anomaly_failsafe::domain::InterlockManager> interlock_mgr);

    ~EdgeCommandFacade() override = default;

    void execute_manual_estop(const std::string& reason) override;
    RecoveryExecutionResultDto resume_recovery_sequence(const std::string& sequence_script) override;
    bool reset_estop_interlock(bool is_field_inspected, bool is_manager_approved) override;

   private:
    std::shared_ptr<anomaly_failsafe::application::EvaluateTelemetryFailsafeUseCase> _evaluate_uc;
    std::shared_ptr<anomaly_failsafe::application::TriggerManualEstopUseCase> _manual_estop_uc;
    std::shared_ptr<anomaly_failsafe::application::ExecuteRecoverySequenceUseCase> _recovery_uc;
    std::shared_ptr<anomaly_failsafe::application::ResetInterlockUseCase> _reset_uc;
    std::shared_ptr<anomaly_failsafe::domain::InterlockManager> _interlock_mgr;
};

}  // namespace sftwin::edge_control
