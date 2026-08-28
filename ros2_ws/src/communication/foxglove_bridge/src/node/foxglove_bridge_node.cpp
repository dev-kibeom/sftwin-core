#include "foxglove_bridge/node/foxglove_bridge_node.hpp"
#include <chrono>
#include <cstring>
#include <nlohmann/json.hpp>

namespace sftwin::plugins::foxglove_bridge {

FoxgloveBridgeNode::FoxgloveBridgeNode(const rclcpp::NodeOptions& options)
    : Node("foxglove_bridge_node", options) {
    initialize_parameters();
    setup_bridge();
}

FoxgloveBridgeNode::~FoxgloveBridgeNode() {
    _server.stop();
}

void FoxgloveBridgeNode::initialize_parameters() {
    // Mermaid 다이어그램 명세에 맞춘 기본 화이트리스트 토픽 목록
    std::vector<std::string> default_whitelist = {
        "/joint_states",
        "/tf",
        "/tf_static",
        "/vision/detections",
        "/failsafe/estop",
        "/telemetry/status"
    };

    this->declare_parameter<int>("port", 8765);
    this->declare_parameter<int>("server.port", 8765);
    this->declare_parameter<std::string>("address", "0.0.0.0");
    this->declare_parameter<std::string>("server.address", "0.0.0.0");
    this->declare_parameter<std::vector<std::string>>("whitelist_topics", default_whitelist);
    this->declare_parameter<std::vector<std::string>>("streaming.topic_whitelist", default_whitelist);

    int s_port = this->get_parameter("server.port").as_int();
    int p_port = this->get_parameter("port").as_int();
    _port = static_cast<uint16_t>(s_port != 8765 ? s_port : p_port);

    std::string s_addr = this->get_parameter("server.address").as_string();
    std::string p_addr = this->get_parameter("address").as_string();
    _address = (s_addr != "0.0.0.0") ? s_addr : p_addr;

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

void FoxgloveBridgeNode::setup_bridge() {
    _server.set_endpoint_handler(this);
    _channel_manager = std::make_unique<DynamicTopicChannelManager>(this);

    // [바이너리 프레이밍]: 13바이트 헤더(Opcode 0x01 + Channel ID + Timestamp) + CDR Buffer
    _channel_manager->set_message_callback(
        [this](ChannelId id, uint64_t timestamp_ns, const uint8_t* payload, size_t size) {
            if (!_server.is_running() || size == 0) return;

            constexpr size_t HEADER_SIZE = 1 + 4 + 8;
            std::vector<uint8_t> frame(HEADER_SIZE + size);

            frame[0] = 0x01;
            std::memcpy(&frame[1], &id, sizeof(uint32_t));
            std::memcpy(&frame[5], &timestamp_ns, sizeof(uint64_t));
            std::memcpy(&frame[HEADER_SIZE], payload, size);

            _server.broadcast_binary(frame.data(), frame.size());
        }
    );

    _channel_manager->discover_and_advertise_topics(_whitelist_topics);
    _server.start(_port, _address);
}

void FoxgloveBridgeNode::on_client_connected(ClientHandle client_hdl) {
    _session_manager.add_client(client_hdl);

    // 1. Server Info 전송
    nlohmann::json server_info = {
        {"op", "serverInfo"},
        {"name", "sftwin_foxglove_bridge"},
        {"capabilities", {"clientPublish", "connectionGraph"}},
        {"supportedEncodings", {"cdr"}}
    };
    _server.send_text(client_hdl, server_info.dump());

    // 2. Advertise 채널 목록 전송
    if (_channel_manager) {
        std::string advertise_json = _channel_manager->generate_advertise_json();
        _server.send_text(client_hdl, advertise_json);
    }
}

void FoxgloveBridgeNode::on_client_disconnected(ClientHandle client_hdl) {
    _session_manager.remove_client(client_hdl);
}

void FoxgloveBridgeNode::on_client_subscribed(ChannelId channel_id, ClientHandle client_hdl) {
    (void)channel_id;
    (void)client_hdl;
}

void FoxgloveBridgeNode::handle_client_message(ClientHandle client_hdl, const std::string& payload_json) {
    try {
        nlohmann::json parsed = nlohmann::json::parse(payload_json);

        // 클라이언트 subscribe 제어 메시지 처리
        if (parsed.contains("op") && parsed["op"] == "subscribe") {
            if (parsed.contains("subscriptions") && parsed["subscriptions"].is_array()) {
                for (const auto& sub : parsed["subscriptions"]) {
                    if (sub.contains("channelId")) {
                        on_client_subscribed(sub["channelId"].get<ChannelId>(), client_hdl);
                    }
                }
            }
        }
    } catch (const std::exception& e) {
        RCLCPP_WARN(this->get_logger(), "Failed to parse client control message: %s", e.what());
    }
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
