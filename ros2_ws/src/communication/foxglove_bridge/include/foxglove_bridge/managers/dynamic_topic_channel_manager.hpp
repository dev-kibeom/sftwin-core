#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>
#include <nlohmann/json.hpp>

#include <rclcpp/rclcpp.hpp>
#include <rclcpp/generic_subscription.hpp>
#include "foxglove_bridge/domain/foxglove_channel.hpp"
#include "foxglove_bridge/interfaces/i_foxglove_bridge_endpoint.hpp"

namespace sftwin::plugins::foxglove_bridge {

using MessageDispatchCallback = std::function<void(ChannelId, uint64_t timestamp_ns, const uint8_t*, size_t)>;

class DynamicTopicChannelManager {
public:
    explicit DynamicTopicChannelManager(rclcpp::Node* node);
    ~DynamicTopicChannelManager() = default;

    DynamicTopicChannelManager(const DynamicTopicChannelManager&) = delete;
    DynamicTopicChannelManager& operator=(const DynamicTopicChannelManager&) = delete;

    ChannelId register_topic(const std::string& topic_name, const std::string& type_name);
    void discover_and_advertise_topics(const std::vector<std::string>& whitelist);
    void set_message_callback(MessageDispatchCallback cb);

    // Foxglove Advertise JSON 생성
    [[nodiscard]] std::string generate_advertise_json() const;
    [[nodiscard]] ChannelId get_channel_id(const std::string& topic_name) const;
    [[nodiscard]] size_t registered_channel_count() const;

private:
    rclcpp::Node* _node{nullptr};
    mutable std::mutex _mutex;
    ChannelId _next_channel_id{1};
    std::unordered_map<std::string, ChannelId> _topic_to_channel;
    std::unordered_map<ChannelId, FoxgloveChannel> _channels;
    std::unordered_map<ChannelId, rclcpp::GenericSubscription::SharedPtr> _subscriptions;
    MessageDispatchCallback _dispatch_cb{nullptr};
};

}  // namespace sftwin::plugins::foxglove_bridge
