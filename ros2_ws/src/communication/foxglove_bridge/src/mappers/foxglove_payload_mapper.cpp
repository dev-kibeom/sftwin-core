#include "foxglove_bridge/mappers/foxglove_payload_mapper.hpp"

namespace sftwin::plugins::foxglove_bridge {

ChannelSchemaInfo FoxglovePayloadMapper::to_channel_schema(const std::string& type_name) const {
    ChannelSchemaInfo info;
    info.schema_name = type_name;
    info.encoding = "cdr";
    return info;
}

shared_interfaces::msg::FailsafeCommand FoxglovePayloadMapper::to_failsafe_command(const std::string& client_json) const {
    nlohmann::json parsed_json;
    try {
        parsed_json = nlohmann::json::parse(client_json);
    } catch (const nlohmann::json::parse_error& e) {
        throw std::invalid_argument(std::string("Invalid JSON syntax: ") + e.what());
    }

    if (!parsed_json.is_object() || !parsed_json.contains("action") || !parsed_json["action"].is_string()) {
        throw std::invalid_argument("Missing or invalid mandatory field 'action'");
    }

    shared_interfaces::msg::FailsafeCommand command;
    command.action_type = parsed_json["action"].get<std::string>();

    if (parsed_json.contains("target") && parsed_json["target"].is_string()) {
        command.target_device_id = parsed_json["target"].get<std::string>();
    } else {
        command.target_device_id = "ALL";
    }

    if (parsed_json.contains("reason") && parsed_json["reason"].is_string()) {
        command.trigger_reason = parsed_json["reason"].get<std::string>();
    } else {
        command.trigger_reason = "WEB_REMOTE_COMMAND";
    }

    auto now = std::chrono::system_clock::now().time_since_epoch();
    command.issued_timestamp_ns = static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(now).count()
    );

    return command;
}

}  // namespace sftwin::plugins::foxglove_bridge
