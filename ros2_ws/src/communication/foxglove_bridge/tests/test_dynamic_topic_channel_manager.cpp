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
        manager = std::make_unique<DynamicTopicChannelManager>(node);
    }

    void TearDown() override {
        manager.reset();
        node.reset();
        rclcpp::shutdown();
    }

    rclcpp::Node::SharedPtr node;
    std::unique_ptr<DynamicTopicChannelManager> manager;
};

// 시나리오 1: 토픽 등록 및 유효한 Foxglove 채널 ID 발급 검증 (Happy Path)
TEST_F(DynamicTopicChannelManagerTest, RegisterTopicAndRetrieveChannelId) {
    // Given: 등록할 토픽 명세
    std::string topic_name = "/joint_states";
    std::string type_name = "sensor_msgs/msg/JointState";

    // When: 토픽 등록 및 채널 ID 발급
    ChannelId ch_id = manager->register_topic(topic_name, type_name);

    // Then: 유효한 ID(>0) 반환 및 동일 토픽에 대해 동일 ID 반환 확인
    EXPECT_GT(ch_id, 0U);
    EXPECT_EQ(manager->get_channel_id(topic_name), ch_id);
    EXPECT_EQ(manager->registered_channel_count(), 1U);
}

// 시나리오 2: 화이트리스트 기반 토픽 탐색 및 광고 검증 (Happy Path)
TEST_F(DynamicTopicChannelManagerTest, DiscoverAndAdvertiseWhitelistedTopics) {
    // Given: 화이트리스트 목록 구성
    std::vector<std::string> whitelist = {
        "/joint_states",
        "/tf",
        "/vision/detections"
    };

    // When: 화이트리스트 기반 토픽 광고 수행
    manager->discover_and_advertise_topics(whitelist);

    // Then: 화이트리스트의 모든 토픽이 채널로 등록됨
    EXPECT_EQ(manager->registered_channel_count(), 3U);
    EXPECT_GT(manager->get_channel_id("/joint_states"), 0U);
    EXPECT_GT(manager->get_channel_id("/tf"), 0U);
    EXPECT_GT(manager->get_channel_id("/vision/detections"), 0U);

    // 비인가/미포함 토픽은 채널 ID가 0이어야 함
    EXPECT_EQ(manager->get_channel_id("/unauthorized/topic"), 0U);
}

// 시나리오 3: 미등록 토픽 조회 시 무효 채널 ID(0) 반환 검증 (Edge Case)
TEST_F(DynamicTopicChannelManagerTest, ReturnZeroForUnregisteredTopic) {
    // Given & When: 미등록 토픽 조회
    ChannelId ch_id = manager->get_channel_id("/unknown/topic");

    // Then: 0 반환 확인
    EXPECT_EQ(ch_id, 0U);
}
