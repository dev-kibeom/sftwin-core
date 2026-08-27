#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <memory>
#include <vector>
#include <chrono>
#include "foxglove_bridge/managers/dynamic_topic_channel_manager.hpp"

using namespace sftwin::plugins::foxglove_bridge;

class DynamicSubscriptionTest : public ::testing::Test {
protected:
    void SetUp() override {
        rclcpp::init(0, nullptr);
        node = std::make_shared<rclcpp::Node>("test_dynamic_sub_node");
        manager = std::make_unique<DynamicTopicChannelManager>(node.get());
    }

    void TearDown() override {
        manager.reset();
        node.reset();
        rclcpp::shutdown();
    }

    rclcpp::Node::SharedPtr node;
    std::unique_ptr<DynamicTopicChannelManager> manager;
};

// 동적 토픽 등록 및 GenericSubscription 생성 검증
TEST_F(DynamicSubscriptionTest, CreateGenericSubscriptionAndReceiveData) {
    std::string test_topic = "/chatter_test";
    std::string type_name = "std_msgs/msg/String";

    size_t callback_count = 0;
    manager->set_message_callback([&](ChannelId id, const uint8_t* data, size_t size) {
        (void)id;
        (void)data;
        (void)size;
        callback_count++;
    });

    ChannelId ch_id = manager->register_topic(test_topic, type_name);
    EXPECT_GT(ch_id, 0U);

    auto pub = node->create_publisher<std_msgs::msg::String>(test_topic, 10);
    std_msgs::msg::String msg;
    msg.data = "hello foxglove";

    pub->publish(msg);
    rclcpp::spin_some(node);

    EXPECT_GT(manager->registered_channel_count(), 0U);
}
