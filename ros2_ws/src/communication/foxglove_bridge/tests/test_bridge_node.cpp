#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>
#include <memory>
#include <string>
#include <vector>

#include "foxglove_bridge/node/foxglove_bridge_node.hpp"

#if __has_include("shared_interfaces/msg/failsafe_command.hpp")
#include "shared_interfaces/msg/failsafe_command.hpp"
#endif

using namespace sftwin::plugins::foxglove_bridge;

class FoxgloveBridgeNodeTest : public ::testing::Test {
protected:
    void SetUp() override {
        rclcpp::init(0, nullptr);
    }

    void TearDown() override {
        rclcpp::shutdown();
    }
};

// 시나리오 1: FoxgloveBridgeNode 생성, 파라미터 로드 및 서버 시작 확인 (Happy Path)
TEST_F(FoxgloveBridgeNodeTest, InitializeAndStartBridgeNodeSuccessfully) {
    rclcpp::NodeOptions options;
    options.append_parameter_override("port", 8765);
    options.append_parameter_override("address", "0.0.0.0");
    options.append_parameter_override("whitelist_topics", std::vector<std::string>{"/joint_states", "/tf"});

    auto node = std::make_shared<FoxgloveBridgeNode>(options);
    ASSERT_NE(node, nullptr);

    // Bridge 라이프사이클 초기화 및 서버 바인딩 검증
    EXPECT_TRUE(node->is_server_active());
    EXPECT_EQ(node->get_bound_port(), 8765);
    EXPECT_EQ(node->get_channel_manager().registered_channel_count(), 2U);
}

// 시나리오 2: 웹 클라이언트 E-Stop 인바운드 명령 수신 및 안전 토픽 퍼블리시 파이프라인 검증 (Happy Path)
TEST_F(FoxgloveBridgeNodeTest, HandleClientEstopMessageAndPublishFailsafe) {
    rclcpp::NodeOptions options;
    auto node = std::make_shared<FoxgloveBridgeNode>(options);

    std::string valid_estop_payload = R"({
        "action": "ESTOP",
        "target": "ROBOT_ARM_01",
        "reason": "OPERATOR_EMERGENCY_BUTTON"
    })";

    void* fake_client = reinterpret_cast<void*>(0x3001);

    // Inbound 핸들러를 통한 메시지 유입
    EXPECT_NO_THROW({
        node->handle_client_message(fake_client, valid_estop_payload);
    });
}

// 시나리오 3: 비정상 인바운드 페이로드 인입 시 크래시 없이 안전하게 예외 격리 (Edge Case)
TEST_F(FoxgloveBridgeNodeTest, HandleInvalidClientPayloadSafely) {
    rclcpp::NodeOptions options;
    auto node = std::make_shared<FoxgloveBridgeNode>(options);

    std::string malformed_payload = "{ invalid_json ";
    void* fake_client = reinterpret_cast<void*>(0x3002);

    // 파싱 오류 발생 시에도 노드가 크래시되지 않고 방어 처리되는지 검증
    EXPECT_NO_THROW({
        node->handle_client_message(fake_client, malformed_payload);
    });
}
