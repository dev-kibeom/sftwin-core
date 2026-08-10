#pragma once
#include <memory>
#include <string>

#include "src/edge_control/anomaly_failsafe/application/trigger_failsafe/trigger_failsafe_usecase.hpp"

namespace sftwin::edge_control::facades {

class EdgeCommandFacadeCPP {
   private:
    std::shared_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> _failsafe_uc;

   public:
    explicit EdgeCommandFacadeCPP(
        std::shared_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> failsafe_uc);

    void execute_failsafe_estop_native(const char* reason);
    bool resume_process_native(const std::string& script);
};

}  // namespace sftwin::edge_control::facades
