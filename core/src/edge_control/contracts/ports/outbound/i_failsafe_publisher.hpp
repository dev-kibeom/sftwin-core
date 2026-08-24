#pragma once

#include <string>

#include "edge_control/contracts/dtos/failsafe_command_dto.hpp"

namespace sftwin::edge_control {

class IFailsafePublisher {
   public:
    virtual ~IFailsafePublisher() = default;

    virtual bool publish(const std::string& topic, const FailsafeCommandDto& data) = 0;
};

}  // namespace sftwin::edge_control
