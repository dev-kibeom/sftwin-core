#include "foxglove_bridge/managers/dynamic_topic_channel_manager.hpp"
#include <chrono>

namespace sftwin::plugins::foxglove_bridge {

DynamicTopicChannelManager::DynamicTopicChannelManager(rclcpp::Node* node)
    : _node(node) {}

void DynamicTopicChannelManager::set_message_callback(MessageDispatchCallback cb) {
    std::lock_guard<std::mutex> lock(_mutex);
    _dispatch_cb = std::move(cb);
}

ChannelId DynamicTopicChannelManager::register_topic(const std::string& topic_name, const std::string& type_name) {
    if (topic_name.empty() || type_name.empty()) {
        return 0;
    }

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

    if (_node != nullptr) {
        try {
            auto sub = _node->create_generic_subscription(
                topic_name,
                type_name,
                rclcpp::QoS(10),
                [this, new_id](std::shared_ptr<const rclcpp::SerializedMessage> serialized_msg) {
                    if (_dispatch_cb && serialized_msg) {
                        auto now_ns = static_cast<uint64_t>(
                            std::chrono::duration_cast<std::chrono::nanoseconds>(
                                std::chrono::system_clock::now().time_since_epoch()
                            ).count()
                        );
                        const auto& rcl_msg = serialized_msg->get_rcl_serialized_message();
                        _dispatch_cb(new_id, now_ns, rcl_msg.buffer, rcl_msg.buffer_length);
                    }
                }
            );
            _subscriptions[new_id] = sub;
        } catch (const std::exception& e) {
            if (_node) {
                RCLCPP_WARN(_node->get_logger(), "Failed to create generic subscription for %s: %s", topic_name.c_str(), e.what());
            }
        }
    }

    return new_id;
}

void DynamicTopicChannelManager::discover_and_advertise_topics(const std::vector<std::string>& whitelist) {
    if (!_node) return;

    const auto topic_names_and_types = _node->get_topic_names_and_types();

    for (const auto& topic : whitelist) {
        auto it = topic_names_and_types.find(topic);
        if (it != topic_names_and_types.end() && !it->second.empty()) {
            register_topic(topic, it->second[0]);
        } else {
            std::string fallback_type = "sensor_msgs/msg/JointState";
            if (topic.find("tf") != std::string::npos) {
                fallback_type = "tf2_msgs/msg/TFMessage";
            } else if (topic.find("vision") != std::string::npos) {
                fallback_type = "vision_msgs/msg/Detection3DArray";
            } else if (topic.find("failsafe") != std::string::npos || topic.find("estop") != std::string::npos) {
                fallback_type = "shared_interfaces/msg/FailsafeCommand";
            }
            register_topic(topic, fallback_type);
        }
    }
}

std::string DynamicTopicChannelManager::generate_advertise_json() const {
    std::lock_guard<std::mutex> lock(_mutex);

    nlohmann::json root;
    root["op"] = "advertise";
    root["channels"] = nlohmann::json::array();

    for (const auto& [id, ch] : _channels) {
        nlohmann::json ch_obj;
        ch_obj["id"] = ch.id;
        ch_obj["topic"] = ch.topic;
        ch_obj["encoding"] = ch.encoding;
        ch_obj["schemaName"] = ch.schema_name;
        root["channels"].push_back(ch_obj);
    }

    return root.dump();
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
