#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include <rclcpp/rclcpp.hpp>

#include "foxglove_bridge/interfaces/i_foxglove_bridge_endpoint.hpp"
#include "foxglove_bridge/mappers/foxglove_payload_mapper.hpp"
#include "foxglove_bridge/managers/client_session_manager.hpp"
#include "foxglove_bridge/managers/dynamic_topic_channel_manager.hpp"
#include "foxglove_bridge/server/foxglove_server_wrapper.hpp"

#if __has_include("shared_interfaces/msg/failsafe_command.hpp")
#include "shared_interfaces/msg/failsafe_command.hpp"
#endif

namespace sftwin::plugins::foxglove_bridge {

class FoxgloveBridgeNode : public rclcpp::Node, public IFoxgloveBridgeEndpoint {
public:
    explicit FoxgloveBridgeNode(const rclcpp::NodeOptions& options = rclcpp::NodeOptions());
    ~FoxgloveBridgeNode() override;

    FoxgloveBridgeNode(const FoxgloveBridgeNode&) = delete;
    FoxgloveBridgeNode& operator=(const FoxgloveBridgeNode&) = delete;

    void on_client_connected(ClientHandle client_hdl) override;
    void on_client_disconnected(ClientHandle client_hdl) override;
    void on_client_subscribed(ChannelId channel_id, ClientHandle client_hdl) override;
    void handle_client_message(ClientHandle client_hdl, const std::string& payload_json) override;
    void broadcast_emergency_stop(const std::string& trigger_reason) override;

    [[nodiscard]] bool is_server_active() const noexcept;
    [[nodiscard]] uint16_t get_bound_port() const noexcept;
    [[nodiscard]] const DynamicTopicChannelManager& get_channel_manager() const noexcept;

private:
    void initialize_parameters();
    void setup_publishers();
    void setup_bridge();

    uint16_t _port{8765};
    std::string _address{"0.0.0.0"};
    std::vector<std::string> _whitelist_topics;

    FoxgloveServerWrapper _server;
    ClientSessionManager _session_manager;
    std::unique_ptr<DynamicTopicChannelManager> _channel_manager;
    FoxglovePayloadMapper _payload_mapper;

#if __has_include("shared_interfaces/msg/failsafe_command.hpp")
    rclcpp::Publisher<shared_interfaces::msg::FailsafeCommand>::SharedPtr _failsafe_pub;
#endif
};

}  // namespace sftwin::plugins::foxglove_bridge
