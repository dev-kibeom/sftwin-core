#pragma once

#include <chrono>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <nlohmann/json.hpp>

#if __has_include("shared_interfaces/msg/failsafe_command.hpp")
#include "shared_interfaces/msg/failsafe_command.hpp"
#else
namespace shared_interfaces::msg {
struct FailsafeCommand {
    std::string target_device_id;
    std::string action_type;
    std::string trigger_reason;
    uint64_t issued_timestamp_ns{0};
};
}  // namespace shared_interfaces::msg
#endif

namespace sftwin::plugins::foxglove_bridge {

struct ChannelSchemaInfo {
    std::string schema_name;
    std::string encoding;
};

class FoxglovePayloadMapper {
public:
    FoxglovePayloadMapper() = default;
    ~FoxglovePayloadMapper() = default;

    ChannelSchemaInfo to_channel_schema(const std::string& type_name) const;
    shared_interfaces::msg::FailsafeCommand to_failsafe_command(const std::string& client_json) const;
};

}  // namespace sftwin::plugins::foxglove_bridge
