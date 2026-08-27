#include <gtest/gtest.h>
#include <rclcpp/rclcpp.hpp>

// 빌드 및 기본 런타임 인프라 환경 검증
class InfraSetupTest : public ::testing::Test {
protected:
    void SetUp() override {
        rclcpp::init(0, nullptr);
    }

    void TearDown() override {
        rclcpp::shutdown();
    }
};

// 시나리오 1: C++20 표준 및 ROS 2 기본 런타임 초기화/종료 정합성 검증 (Happy Path)
TEST_F(InfraSetupTest, VerifyRclcppInitializationAndShutdown) {
    // Given: rclcpp가 SetUp에서 초기화됨
    // When: 노드 생성을 시도함
    auto test_node = std::make_shared<rclcpp::Node>("infra_smoke_test_node");

    // Then: 노드가 nullptr가 아니고 정상 노드 이름을 반환함
    ASSERT_NE(test_node, nullptr);
    EXPECT_STREQ(test_node->get_name(), "infra_smoke_test_node");
    EXPECT_TRUE(rclcpp::ok());
}

// 시나리오 2: 패키지 기본 파라미터 컨테이너 연동 검증 (Edge Case / Setup Verification)
TEST_F(InfraSetupTest, VerifyNodeParameterInfrastructure) {
    // Given: 테스트용 ROS 2 노드 생성
    auto test_node = std::make_shared<rclcpp::Node>("infra_param_test_node");

    // When: 기본 파라미터 선언 및 조회
    test_node->declare_parameter<int>("server.port", 8765);
    int port = test_node->get_parameter("server.port").as_int();

    // Then: 설정한 파라미터가 정확히 일치함
    EXPECT_EQ(port, 8765);
}

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
