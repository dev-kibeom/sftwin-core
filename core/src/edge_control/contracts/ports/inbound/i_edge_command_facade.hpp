#pragma once

#include <string>

namespace sftwin::edge_control {

class IEdgeCommandFacade {
   public:
    virtual ~IEdgeCommandFacade() = default;

    virtual void execute_manual_estop(const std::string& reason) = 0;
    virtual RecoveryExecutionResultDto resume_recovery_sequence(const std::string& sequence_script) = 0;
    virtual bool reset_estop_interlock(bool is_field_inspected, bool is_manager_approved) = 0;
};

}  // namespace sftwin::edge_control
