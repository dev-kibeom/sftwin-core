#pragma once

#include <memory>
#include <string>

#include "edge_control/ports/inbound/i_edge_command_facade.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
class TriggerFailsafeUseCase;
class ResetEstopInterlockUseCase;
}

namespace sftwin::edge_control {

class EdgeCommandFacade : public IEdgeCommandFacade {
   public:
    explicit EdgeCommandFacade(
        std::shared_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> failsafe_uc,
        std::shared_ptr<anomaly_failsafe::application::ResetEstopInterlockUseCase> reset_uc);

    ~EdgeCommandFacade() override = default;

    void execute_failsafe_estop(const char* reason) override;
    bool resume_process(const std::string& sequence_script) override;
    bool reset_estop_2step(bool is_field_inspected, bool is_manager_approved) override;

   private:
    std::shared_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> _failsafe_uc;
    std::shared_ptr<anomaly_failsafe::application::ResetEstopInterlockUseCase> _reset_uc;
};

}  // namespace sftwin::edge_control
