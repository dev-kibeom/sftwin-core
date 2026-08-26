// ros2_ws/src/simulation/mujoco_sim/test/test_mujoco_physics_adapter_node.cpp
#include <gtest/gtest.h>
#include <memory>
#include <string>
#include <filesystem>
#include <fstream>
#include <rclcpp/rclcpp.hpp>

#include "mujoco_sim/mujoco_physics_adapter_node.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared_interfaces/srv/simulate_scenario.hpp"
#include "shared_interfaces/msg/failsafe_command.hpp"

namespace fs = std::filesystem;
using namespace sftwin::plugins::mujoco;
using namespace sftwin::shared;

class MujocoPhysicsAdapterNodeTest : public ::testing::Test {
protected:
    static void SetUpTestSuite() {
        if (!rclcpp::ok()) {
            rclcpp::init(0, nullptr);
        }
    }

    static void TearDownTestSuite() {
        if (rclcpp::ok()) {
            rclcpp::shutdown();
        }
    }

    std::string temp_dir_;
    std::string valid_xml_path_;

    void SetUp() override {
        temp_dir_ = (fs::temp_directory_path() / "mj_adapter_node_test_dir").string();
        fs::create_directories(temp_dir_);

        valid_xml_path_ = (fs::path(temp_dir_) / "adapter_test_robot.xml").string();
        std::ofstream valid_file(valid_xml_path_);
        valid_file << "<mujoco model=\"adapter_robot\">\n"
                   << "  <option timestep=\"0.002\" gravity=\"0 0 -9.81\"/>\n"
                   << "  <worldbody>\n"
                   << "    <body name=\"link1\" pos=\"0 0 0.5\">\n"
                   << "      <joint name=\"joint1\" type=\"hinge\" axis=\"0 0 1\"/>\n"
                   << "      <geom name=\"geom1\" type=\"box\" size=\"0.1 0.1 0.1\" mass=\"1.0\"/>\n"
                   << "    </body>\n"
                   << "  </worldbody>\n"
                   << "</mujoco>";
        valid_file.close();
    }

    void TearDown() override {
        fs::remove_all(temp_dir_);
    }
};

TEST_F(MujocoPhysicsAdapterNodeTest, HandleSimulateScenario_ValidRequest_ReturnsSuccessResponse) {
    // Given
    rclcpp::NodeOptions options;
    auto node = std::make_shared<MujocoPhysicsAdapterNode>(options);
    auto request = std::make_shared<shared_interfaces::srv::SimulateScenario::Request>();
    auto response = std::make_shared<shared_interfaces::srv::SimulateScenario::Response>();

    request->scenario_id = "SCENARIO_001";
    request->baseline_id = "BASELINE_001";
    request->model_file_path = valid_xml_path_;
    request->dt_sec = 0.002;
    request->max_duration_sec = 0.01;
    request->joint_damping = 0.5;
    request->friction_loss = 0.1;

    // When
    node->handle_simulate_scenario(request, response);

    // Then
    EXPECT_TRUE(response->is_success);
    EXPECT_EQ(response->collision_count, 0);
    EXPECT_GT(response->trajectory_points.size(), 0);
    EXPECT_TRUE(response->error_message.empty());
}

TEST_F(MujocoPhysicsAdapterNodeTest, HandleSimulateScenario_InvalidFilePath_ReturnsFailureResponse) {
    // Given
    rclcpp::NodeOptions options;
    auto node = std::make_shared<MujocoPhysicsAdapterNode>(options);
    auto request = std::make_shared<shared_interfaces::srv::SimulateScenario::Request>();
    auto response = std::make_shared<shared_interfaces::srv::SimulateScenario::Response>();

    request->scenario_id = "SCENARIO_002";
    request->model_file_path = "/invalid/path/non_existent.xml";
    request->max_duration_sec = 0.01;

    // When
    node->handle_simulate_scenario(request, response);

    // Then
    EXPECT_FALSE(response->is_success);
    EXPECT_FALSE(response->error_message.empty());
}

TEST_F(MujocoPhysicsAdapterNodeTest, TriggerFailsafeStop_DirectCall_LocksEngine) {
    // Given
    rclcpp::NodeOptions options;
    auto node = std::make_shared<MujocoPhysicsAdapterNode>(options);

    // When
    node->trigger_failsafe_stop();

    // Then
    EXPECT_TRUE(node->is_simulation_locked());
}

TEST_F(MujocoPhysicsAdapterNodeTest, FailsafeEstopCallback_MsgReceived_LocksEngine) {
    // Given
    rclcpp::NodeOptions options;
    auto node = std::make_shared<MujocoPhysicsAdapterNode>(options);
    shared_interfaces::msg::FailsafeCommand msg;
    msg.action_type = "ESTOP";
    msg.trigger_reason = "Emergency Stop Requested";

    // When
    node->on_failsafe_estop_received(msg);

    // Then
    EXPECT_TRUE(node->is_simulation_locked());
}
