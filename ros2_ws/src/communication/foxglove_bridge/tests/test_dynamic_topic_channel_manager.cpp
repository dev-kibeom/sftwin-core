#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>
#include <memory>
#include <vector>
#include <string>

#include "foxglove_bridge/managers/dynamic_topic_channel_manager.hpp"

using namespace sftwin::plugins::foxglove_bridge;

class DynamicTopicChannelManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        rclcpp::init(0, nullptr);
        node = std::make_shared<rclcpp::Node>("test_channel_mgr_node");
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

TEST_F(DynamicTopicChannelManagerTest, RegisterTopicAndRetrieveChannelId) {
    std::string topic_name = "/joint_states";
    std::string type_name = "sensor_msgs/msg/JointState";

    ChannelId ch_id = manager->register_topic(topic_name, type_name);

    EXPECT_GT(ch_id, 0U);
    EXPECT_EQ(manager->get_channel_id(topic_name), ch_id);
    EXPECT_EQ(manager->registered_channel_count(), 1U);
}

TEST_F(DynamicTopicChannelManagerTest, DiscoverAndAdvertiseWhitelistedTopics) {
    std::vector<std::string> whitelist = {
        "/joint_states",
        "/tf",
        "/vision/detections"
    };

    manager->discover_and_advertise_topics(whitelist);

    EXPECT_EQ(manager->registered_channel_count(), 3U);
    EXPECT_GT(manager->get_channel_id("/joint_states"), 0U);
    EXPECT_GT(manager->get_channel_id("/tf"), 0U);
    EXPECT_GT(manager->get_channel_id("/vision/detections"), 0U);
    EXPECT_EQ(manager->get_channel_id("/unauthorized/topic"), 0U);
}

TEST_F(DynamicTopicChannelManagerTest, ReturnZeroForUnregisteredTopic) {
    ChannelId ch_id = manager->get_channel_id("/unknown/topic");
    EXPECT_EQ(ch_id, 0U);
}
