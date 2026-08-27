#pragma once

#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include "foxglove_bridge/domain/foxglove_channel.hpp"
#include "foxglove_bridge/interfaces/i_foxglove_bridge_endpoint.hpp"

namespace sftwin::plugins::foxglove_bridge {

class DynamicTopicChannelManager {
public:
    explicit DynamicTopicChannelManager(rclcpp::Node::SharedPtr node);
    ~DynamicTopicChannelManager() = default;

    DynamicTopicChannelManager(const DynamicTopicChannelManager&) = delete;
    DynamicTopicChannelManager& operator=(const DynamicTopicChannelManager&) = delete;

    ChannelId register_topic(const std::string& topic_name, const std::string& type_name);
    void discover_and_advertise_topics(const std::vector<std::string>& whitelist);

    [[nodiscard]] ChannelId get_channel_id(const std::string& topic_name) const;
    [[nodiscard]] size_t registered_channel_count() const;

private:
    rclcpp::Node::SharedPtr _node;
    mutable std::mutex _mutex;
    ChannelId _next_channel_id{1};
    std::unordered_map<std::string, ChannelId> _topic_to_channel;
    std::unordered_map<ChannelId, FoxgloveChannel> _channels;
};

}  // namespace sftwin::plugins::foxglove_bridge
