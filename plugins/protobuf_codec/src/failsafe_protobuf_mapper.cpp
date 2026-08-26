#include "plugins/protobuf_codec/include/failsafe_protobuf_mapper.hpp"

#include <chrono>
#include <stdexcept>

namespace sftwin::plugins::protobuf_codec {
using namespace sftwin::failsafe;
using namespace sftwin::edge_control::anomaly_failsafe;

FailsafeCommandProto FailsafeProtobufMapper::to_protobuf(
    domain::FailsafeAction action, const std::string& target_id,
    const std::string& reason) const {
    FailsafeCommandProto proto;
    proto.set_target_device_id(target_id);
    proto.set_trigger_reason(reason);

    auto now = std::chrono::steady_clock::now().time_since_epoch();
    proto.set_issued_timestamp_ns(
        std::chrono::duration_cast<std::chrono::nanoseconds>(now).count());

    switch (action) {
        case domain::FailsafeAction::ESTOP:
            proto.set_action_type("ESTOP");
            break;
        case domain::FailsafeAction::RESUME:
            proto.set_action_type("RESUME");
            break;
        case domain::FailsafeAction::BYPASS:
            proto.set_action_type("BYPASS");
            break;
        case domain::FailsafeAction::PAUSE:
            proto.set_action_type("PAUSE");
            break;
        default:
            proto.set_action_type("NONE");
            break;
    }

    return proto;
}

}  // namespace sftwin::plugins::protobuf_codec
