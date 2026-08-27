#pragma once

#include <cstdint>

namespace sftwin::plugins::foxglove_bridge {

enum class FoxgloveConnectionState {
    DISCONNECTED,
    LISTENING,
    CLIENT_CONNECTED,
    DRAINING,
    SHUTTING_DOWN
};

enum class ChannelEncoding {
    CDR,
    JSON,
    PROTOBUF,
    FLATBUFFERS
};

enum class WebClientCommandType {
    TRIGGER_ESTOP,
    RELEASE_ESTOP,
    START_SCENARIO,
    PAUSE_SIMULATION,
    SET_PARAMETER,
    TRIGGER_BT_RECOVERY
};

enum class BackpressurePolicy {
    DROP_OLDEST,
    DROP_NEWEST,
    THROTTLE_RATE,
    DISCONNECT_CLIENT
};

}  // namespace sftwin::plugins::foxglove_bridge
