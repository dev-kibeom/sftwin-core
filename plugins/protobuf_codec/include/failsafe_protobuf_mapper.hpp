#pragma once

#include <string>

#include "failsafe_command.pb.h"

#include "core/src/edge_control/anomaly_failsafe/domain/failsafe_evaluation/failsafe_rule.hpp"
#include "core/src/edge_control/anomaly_failsafe/domain/failsafe_evaluation/failsafe_action_enum.hpp"

namespace sftwin::plugins::protobuf_codec {

class FailsafeProtobufMapper {
   public:
    FailsafeProtobufMapper() = default;
    ~FailsafeProtobufMapper() = default;

    sftwin::failsafe::FailsafeCommandProto to_protobuf(
        edge_control::anomaly_failsafe::domain::FailsafeAction action,
        const std::string& target_id,
        const std::string& reason) const;
};

}  // namespace sftwin::plugins::protobuf_codec
