#pragma once

#include <string>

#include "failsafe_command.pb.h"

#include "core/src/edge_control/anomaly_failsafe/domain/failsafe_rule.hpp"
#include "core/src/edge_control/anomaly_failsafe/domain/edge_local_enums.hpp"

namespace sftwin::plugins::protobuf_codec {

class FailsafeProtobufMapper {
   public:
    FailsafeProtobufMapper() = default;
    ~FailsafeProtobufMapper() = default;

    // domain::FailsafeActionEnum 및 상태 파라미터를 Protobuf FailsafeCommandProto 객체로 변환
    sftwin::failsafe::FailsafeCommandProto to_protobuf(
        edge_control::anomaly_failsafe::domain::FailsafeActionEnum action,
        const std::string& target_id,
        const std::string& reason) const;
};

}  // namespace sftwin::plugins::protobuf_codec
