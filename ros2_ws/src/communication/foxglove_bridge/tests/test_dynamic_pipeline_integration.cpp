#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <memory>
#include <string>
#include <vector>
#include <chrono>

#include "foxglove_bridge/managers/dynamic_topic_channel_manager.hpp"

using namespace sftwin::plugins::foxglove_bridge;
using namespace std::chrono_literals;

class DynamicPipelineIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        rclcpp::init(0, nullptr);
        node = std::make_shared<rclcpp::Node>("test_dynamic_pipeline_node");
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

TEST_F(DynamicPipelineIntegrationTest, DiscoverActiveTopicFromGraph) {
    auto pub = node->create_publisher<std_msgs::msg::String>("/graph_topic", 10);

    manager->discover_and_advertise_topics({"/graph_topic"});

    ChannelId ch_id = manager->get_channel_id("/graph_topic");
    EXPECT_GT(ch_id, 0U);
    EXPECT_EQ(manager->registered_channel_count(), 1U);
}

TEST_F(DynamicPipelineIntegrationTest, ReceiveSerializedMessageViaCallback) {
    bool callback_executed = false;
    ChannelId captured_channel = 0;
    uint64_t captured_timestamp = 0;
    size_t captured_size = 0;

    manager->set_message_callback(
        [&](ChannelId id, uint64_t timestamp_ns, const uint8_t* data, size_t size) {
            callback_executed = true;
            captured_channel = id;
            captured_timestamp = timestamp_ns;
            captured_size = size;
            EXPECT_NE(data, nullptr);
            EXPECT_GT(timestamp_ns, 0ULL);
            EXPECT_GT(size, 0U);
        }
    );

    ChannelId ch_id = manager->register_topic("/test_stream_topic", "std_msgs/msg/String");
    EXPECT_GT(ch_id, 0u);

    // 메시지 발행 후 spin_some으로 콜백 강제 실행
    auto pub = node->create_publisher<std_msgs::msg::String>("/test_stream_topic", 10);
    std_msgs::msg::String msg;
    msg.data = "telemetry_test_payload";

    pub->publish(msg);
    rclcpp::spin_some(node);

    EXPECT_TRUE(callback_executed);
    EXPECT_EQ(captured_channel, ch_id);
    EXPECT_GT(captured_size, 0U);
}
