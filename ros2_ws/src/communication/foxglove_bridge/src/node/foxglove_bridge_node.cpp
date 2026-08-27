#include "foxglove_bridge/node/foxglove_bridge_node.hpp"
#include <chrono>

namespace sftwin::plugins::foxglove_bridge {

FoxgloveBridgeNode::FoxgloveBridgeNode(const rclcpp::NodeOptions& options)
    : Node("foxglove_bridge_node", options) {
    initialize_parameters();
    setup_publishers();
    setup_bridge();
}

FoxgloveBridgeNode::~FoxgloveBridgeNode() {
    _server.stop();
}

void FoxgloveBridgeNode::initialize_parameters() {
    std::vector<std::string> default_whitelist = {
        "/joint_states",
        "/tf",
        "/tf_static",
        "/vision/detections",
        "/failsafe/status",
        "/manipulator/trajectory",
        "/rmf/fleet_states"
    };

    this->declare_parameter<int>("port", 8765);
    this->declare_parameter<int>("server.port", 8765);
    this->declare_parameter<std::string>("address", "0.0.0.0");
    this->declare_parameter<std::string>("server.address", "0.0.0.0");
    this->declare_parameter<std::vector<std::string>>("whitelist_topics", default_whitelist);
    this->declare_parameter<std::vector<std::string>>("streaming.topic_whitelist", default_whitelist);

    // 포트 결정
    int s_port = this->get_parameter("server.port").as_int();
    int p_port = this->get_parameter("port").as_int();
    _port = static_cast<uint16_t>(s_port != 8765 ? s_port : p_port);

    // 바인드 주소 결정
    std::string s_addr = this->get_parameter("server.address").as_string();
    std::string p_addr = this->get_parameter("address").as_string();
    _address = (s_addr != "0.0.0.0") ? s_addr : p_addr;

    // 화이트리스트 토픽 결정 (오버라이드된 항목 우선 채택)
    auto p_whitelist = this->get_parameter("whitelist_topics").as_string_array();
    auto s_whitelist = this->get_parameter("streaming.topic_whitelist").as_string_array();

    if (p_whitelist != default_whitelist) {
        _whitelist_topics = p_whitelist;
    } else if (s_whitelist != default_whitelist) {
        _whitelist_topics = s_whitelist;
    } else {
        _whitelist_topics = default_whitelist;
    }
}

void FoxgloveBridgeNode::setup_publishers() {
#if __has_include("shared_interfaces/msg/failsafe_command.hpp")
    _failsafe_pub = this->create_publisher<shared_interfaces::msg::FailsafeCommand>(
        "/safety/failsafe_command",
        rclcpp::QoS(10).reliable()
    );
#endif
}

void FoxgloveBridgeNode::setup_bridge() {
    _channel_manager = std::make_unique<DynamicTopicChannelManager>(this);
    _channel_manager->discover_and_advertise_topics(_whitelist_topics);

    _server.start(_port, _address);
}

void FoxgloveBridgeNode::on_client_connected(ClientHandle client_hdl) {
    _session_manager.add_client(client_hdl);
}

void FoxgloveBridgeNode::on_client_disconnected(ClientHandle client_hdl) {
    _session_manager.remove_client(client_hdl);
}

void FoxgloveBridgeNode::on_client_subscribed(ChannelId channel_id, ClientHandle client_hdl) {
    (void)channel_id;
    (void)client_hdl;
}

void FoxgloveBridgeNode::handle_client_message(ClientHandle client_hdl, const std::string& payload_json) {
    (void)client_hdl;
    try {
        auto command = _payload_mapper.to_failsafe_command(payload_json);
#if __has_include("shared_interfaces/msg/failsafe_command.hpp")
        if (_failsafe_pub) {
            _failsafe_pub->publish(command);
        }
#endif
        RCLCPP_INFO(
            this->get_logger(),
            "Successfully processed and published failsafe command: action=%s, target=%s",
            command.action_type.c_str(),
            command.target_device_id.c_str()
        );
    } catch (const std::exception& e) {
        RCLCPP_WARN(this->get_logger(), "Failed to handle client message: %s", e.what());
    }
}

void FoxgloveBridgeNode::broadcast_emergency_stop(const std::string& trigger_reason) {
#if __has_include("shared_interfaces/msg/failsafe_command.hpp")
    shared_interfaces::msg::FailsafeCommand cmd;
    cmd.target_device_id = "ALL";
    cmd.action_type = "ESTOP";
    cmd.trigger_reason = trigger_reason;
    auto now = std::chrono::system_clock::now().time_since_epoch();
    cmd.issued_timestamp_ns = static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(now).count()
    );

    if (_failsafe_pub) {
        _failsafe_pub->publish(cmd);
    }
#else
    (void)trigger_reason;
#endif
}

bool FoxgloveBridgeNode::is_server_active() const noexcept {
    return _server.is_running();
}

uint16_t FoxgloveBridgeNode::get_bound_port() const noexcept {
    return _server.bound_port();
}

const DynamicTopicChannelManager& FoxgloveBridgeNode::get_channel_manager() const noexcept {
    return *_channel_manager;
}

}  // namespace sftwin::plugins::foxglove_bridge
