#pragma once

#include <string>
#include "edge_control/contracts/dtos/recovery_execution_result_dto.hpp"

namespace sftwin::edge_control {

class IRecoverySequence {
   public:
    virtual ~IRecoverySequence() = default;

    virtual RecoveryExecutionResultDto execute_sequence(const std::string& sequence_script) = 0;
};

}  // namespace sftwin::edge_control
