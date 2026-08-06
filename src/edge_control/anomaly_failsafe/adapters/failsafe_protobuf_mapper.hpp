#pragma once
#include <string>

#include "failsafe_command.pb.h"
#include "src/edge_control/anomaly_failsafe/domain/edge_local_enums.hpp"

namespace sftwin::edge_control::anomaly_failsafe::adapters {

/**
 * @brief 단일 책임 원칙(SRP) 기반 Protobuf 변환 어댑터
 */
class FailsafeProtobufMapper {
   public:
    sftwin::failsafe::FailsafeCommandProto to_protobuf(domain::FailsafeActionEnum action,
                                                       const std::string& target_id,
                                                       const std::string& reason) const;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::adapters