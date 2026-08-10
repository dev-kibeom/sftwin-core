#pragma once
#include <string>

#include "failsafe_command.pb.h"

namespace sftwin::edge_control::anomaly_failsafe::dtos {

class FailsafeCommandDto {
   private:
    sftwin::failsafe::FailsafeCommandProto _proto;

   public:
    FailsafeCommandDto(const std::string& target, const std::string& action,
                       const std::string& reason, uint64_t timestamp) {
        _proto.set_target_device_id(target);
        _proto.set_action_type(action);
        _proto.set_trigger_reason(reason);
        _proto.set_issued_timestamp_ns(timestamp);
    }
    const sftwin::failsafe::FailsafeCommandProto& get_proto() const { return _proto; }
};

}  // namespace sftwin::edge_control::anomaly_failsafe::dtos
