#pragma once

#include <string>

namespace sftwin::edge_control {

class IRecoverySequence {
   public:
    virtual ~IRecoverySequence() = default;

    virtual bool execute_recovery_sequence(const std::string& sequence_script) = 0;
};

}  // namespace sftwin::edge_control
