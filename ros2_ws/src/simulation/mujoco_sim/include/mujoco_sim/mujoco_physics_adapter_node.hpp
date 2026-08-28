// ros2_ws/src/simulation/mujoco_sim/include/mujoco_sim/mujoco_physics_adapter_node.hpp
#pragma once

#include <memory>
#include <string>
#include <vector>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/string.hpp>
#include <tf2_ros/transform_broadcaster.h>

#include "mujoco_sim/mujoco_engine_wrapper.hpp"
#include "mujoco_sim/mujoco_data_mapper.hpp"
#include "shared_interfaces/srv/simulate_scenario.hpp"
#include "shared_interfaces/msg/failsafe_command.hpp"

namespace sftwin::plugins::mujoco {

class IMujocoServiceEndpoint {
public:
    virtual ~IMujocoServiceEndpoint() = default;
    virtual void handle_simulate_scenario(
        const std::shared_ptr<shared_interfaces::srv::SimulateScenario::Request> request,
        std::shared_ptr<shared_interfaces::srv::SimulateScenario::Response> response) = 0;
    virtual void trigger_failsafe_stop() = 0;
};

class MujocoPhysicsAdapterNode : public rclcpp::Node, public IMujocoServiceEndpoint {
public:
    explicit MujocoPhysicsAdapterNode(const rclcpp::NodeOptions& options = rclcpp::NodeOptions());
    ~MujocoPhysicsAdapterNode() override = default;

    void handle_simulate_scenario(
        const std::shared_ptr<shared_interfaces::srv::SimulateScenario::Request> request,
        std::shared_ptr<shared_interfaces::srv::SimulateScenario::Response> response) override;

    void trigger_failsafe_stop() override;
    void on_failsafe_estop_received(const shared_interfaces::msg::FailsafeCommand& msg);
    void publish_simulation_state();

    bool is_simulation_locked() const noexcept;

private:
    std::unique_ptr<MujocoEngineWrapper> engine_wrapper_;
    MujocoDataMapper mapper_;

    rclcpp::Service<shared_interfaces::srv::SimulateScenario>::SharedPtr sim_service_;
    rclcpp::Subscription<shared_interfaces::msg::FailsafeCommand>::SharedPtr estop_sub_;
    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_pub_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr telemetry_pub_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr detection_pub_;
    std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    rclcpp::TimerBase::SharedPtr publish_timer_;

    std::string base_frame_id_{"world"};
    std::string tf_prefix_{"sftwin_"};
    std::string joint_topic_name_{"/joint_states"};
    std::string telemetry_topic_name_{"/telemetry/status"};
    std::string detection_topic_name_{"/vision/detections"};
    double publish_rate_hz_{50.0};
};

}  // namespace sftwin::plugins::mujoco
