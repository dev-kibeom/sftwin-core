#pragma once

#include <string>

namespace sftwin::edge_control {

class IEdgeCommandFacade {
   public:
    virtual ~IEdgeCommandFacade() = default;

    virtual void execute_failsafe_estop(const char* reason) = 0;
    virtual bool resume_process(const std::string& sequence_script) = 0;
    virtual bool reset_estop_2step(bool is_field_inspected, bool is_manager_approved) = 0;
};

}  // namespace sftwin::edge_control
