#include "foxglove_bridge/managers/dynamic_topic_channel_manager.hpp"

namespace sftwin::plugins::foxglove_bridge {

DynamicTopicChannelManager::DynamicTopicChannelManager(rclcpp::Node* node)
    : _node(node) {}

ChannelId DynamicTopicChannelManager::register_topic(const std::string& topic_name, const std::string& type_name) {
    std::lock_guard<std::mutex> lock(_mutex);

    auto it = _topic_to_channel.find(topic_name);
    if (it != _topic_to_channel.end()) {
        return it->second;
    }

    ChannelId new_id = _next_channel_id++;
    _topic_to_channel[topic_name] = new_id;

    FoxgloveChannel channel{};
    channel.id = new_id;
    channel.topic = topic_name;
    channel.encoding = "cdr";
    channel.schema_name = type_name;
    _channels[new_id] = channel;

    return new_id;
}

void DynamicTopicChannelManager::discover_and_advertise_topics(const std::vector<std::string>& whitelist) {
    for (const auto& topic : whitelist) {
        std::string assumed_type = "sensor_msgs/msg/JointState";
        if (topic.find("tf") != std::string::npos) {
            assumed_type = "tf2_msgs/msg/TFMessage";
        } else if (topic.find("vision") != std::string::npos) {
            assumed_type = "vision_msgs/msg/Detection3DArray";
        }
        register_topic(topic, assumed_type);
    }
}

ChannelId DynamicTopicChannelManager::get_channel_id(const std::string& topic_name) const {
    std::lock_guard<std::mutex> lock(_mutex);
    auto it = _topic_to_channel.find(topic_name);
    if (it != _topic_to_channel.end()) {
        return it->second;
    }
    return 0;
}

size_t DynamicTopicChannelManager::registered_channel_count() const {
    std::lock_guard<std::mutex> lock(_mutex);
    return _topic_to_channel.size();
}

}  // namespace sftwin::plugins::foxglove_bridge
