#include "edge_command_facade.hpp"

namespace sftwin::edge_control::facades {

EdgeCommandFacadeCPP::EdgeCommandFacadeCPP(
    std::shared_ptr<anomaly_failsafe::application::TriggerFailsafeUseCase> failsafe_uc)
    : _failsafe_uc(std::move(failsafe_uc)) {}

void EdgeCommandFacadeCPP::execute_failsafe_estop_native(const char* reason) {
    _failsafe_uc->trigger_manual_estop(std::string(reason));
}

bool EdgeCommandFacadeCPP::resume_process_native(const std::string& script) {
    return _failsafe_uc->execute_behavior_tree_recovery(script);
}

}  // namespace sftwin::edge_control::facades
