#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <memory>
#include <string>
#include <vector>

#include "foxglove_bridge/managers/dynamic_topic_channel_manager.hpp"

using namespace sftwin::plugins::foxglove_bridge;

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

// 시나리오 1: 그래프 내 활성 토픽의 자동 타입 감지 및 등록 검증
TEST_F(DynamicPipelineIntegrationTest, DiscoverActiveTopicFromGraph) {
    auto pub = node->create_publisher<std_msgs::msg::String>("/graph_topic", 10);

    // When: 활성 토픽 검색
    manager->discover_and_advertise_topics({"/graph_topic"});

    // Then: 채널 매니저에 정상 등록 확인
    ChannelId ch_id = manager->get_channel_id("/graph_topic");
    EXPECT_GT(ch_id, 0U);
    EXPECT_EQ(manager->registered_channel_count(), 1U);
}

// 시나리오 2: GenericSubscription을 통한 CDR 직렬화 데이터 수신 및 콜백 디스패치 검증
TEST_F(DynamicPipelineIntegrationTest, ReceiveSerializedMessageViaCallback) {
    bool callback_executed = false;
    ChannelId captured_channel = 0;
    size_t captured_size = 0;

    manager->set_message_callback([&](ChannelId id, const uint8_t* data, size_t size) {
        callback_executed = true;
        captured_channel = id;
        captured_size = size;
        EXPECT_NE(data, nullptr);
    });

    ChannelId ch_id = manager->register_topic("/stream_test", "std_msgs/msg/String");
    auto pub = node->create_publisher<std_msgs::msg::String>("/stream_test", 10);

    std_msgs::msg::String msg;
    msg.data = "foxglove_integration_test";
    pub->publish(msg);

    // ROS 2 이벤트 루프 처리
    for (int i = 0; i < 5 && !callback_executed; ++i) {
        rclcpp::spin_some(node);
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }

    EXPECT_TRUE(callback_executed);
    EXPECT_EQ(captured_channel, ch_id);
    EXPECT_GT(captured_size, 0U);
}
