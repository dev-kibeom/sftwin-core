#pragma once
#include <string>

#include "src/edge_control/anomaly_failsafe/ports/outbound/failsafe_command_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::ports {
class IFailsafePublisher {
   public:
    virtual ~IFailsafePublisher() = default;
    virtual bool publish(const std::string& topic, const dtos::FailsafeCommandDto& data) = 0;
};
}  // namespace sftwin::edge_control::anomaly_failsafe::ports
