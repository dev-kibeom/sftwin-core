// ros2_ws/src/simulation/mujoco_sim/src/mujoco_physics_adapter_node.cpp
#include "mujoco_sim/mujoco_physics_adapter_node.hpp"
#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <thread>

#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

namespace sftwin::plugins::mujoco {

MujocoPhysicsAdapterNode::MujocoPhysicsAdapterNode(const rclcpp::NodeOptions& options)
    : Node("sftwin_mujoco_sim_node", options),
      engine_wrapper_(std::make_unique<MujocoEngineWrapper>()),
      mapper_() {

    this->declare_parameter<std::string>("broadcasting.base_frame_id", "world");
    this->declare_parameter<std::string>("broadcasting.tf_prefix", "sftwin_");
    this->declare_parameter<std::string>("broadcasting.joint_topic_name", "/joint_states");
    this->declare_parameter<double>("broadcasting.publish_rate_hz", 50.0);

    this->get_parameter("broadcasting.base_frame_id", base_frame_id_);
    this->get_parameter("broadcasting.tf_prefix", tf_prefix_);
    this->get_parameter("broadcasting.joint_topic_name", joint_topic_name_);
    this->get_parameter("broadcasting.publish_rate_hz", publish_rate_hz_);

    sim_service_ = this->create_service<shared_interfaces::srv::SimulateScenario>(
        "/sftwin/simulate_scenario",
        [this](const std::shared_ptr<shared_interfaces::srv::SimulateScenario::Request> req,
               std::shared_ptr<shared_interfaces::srv::SimulateScenario::Response> res) {
            this->handle_simulate_scenario(req, res);
        });

    estop_sub_ = this->create_subscription<shared_interfaces::msg::FailsafeCommand>(
        "/failsafe/estop",
        rclcpp::QoS(10),
        [this](const shared_interfaces::msg::FailsafeCommand::SharedPtr msg) {
            this->on_failsafe_estop_received(*msg);
        });

    joint_pub_ = this->create_publisher<sensor_msgs::msg::JointState>(joint_topic_name_, rclcpp::QoS(10));
    tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

    auto timer_period = std::chrono::duration<double>(1.0 / publish_rate_hz_);
    publish_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::nanoseconds>(timer_period),
        [this]() { this->publish_simulation_state(); });
}

void MujocoPhysicsAdapterNode::handle_simulate_scenario(
    const std::shared_ptr<shared_interfaces::srv::SimulateScenario::Request> request,
    std::shared_ptr<shared_interfaces::srv::SimulateScenario::Response> response) {
    try {
        if (!engine_wrapper_->load_model_from_file(request->model_file_path)) {
            response->is_success = false;
            response->error_message = "Failed to load model file: " + request->model_file_path;
            return;
        }

        engine_wrapper_->set_dynamics_parameters(request->joint_damping, request->friction_loss);

        double current_time = 0.0;
        double max_duration = request->max_duration_sec;
        double dt = (request->dt_sec > 0.0) ? request->dt_sec : 0.002;
        int total_collisions = 0;

        while (current_time < max_duration && !engine_wrapper_->is_locked()) {
            engine_wrapper_->step_simulation();

            auto contacts = engine_wrapper_->check_contacts();
            bool is_collided = false;
            for (const auto& c : contacts) {
                if (c.is_collided) {
                    is_collided = true;
                    total_collisions++;
                }
            }

            const mjData* d = engine_wrapper_->get_data();
            auto dto = mapper_.to_trajectory_point(d, current_time, request->scenario_id, is_collided);

            shared_interfaces::msg::TrajectoryPoint point_msg;
            point_msg.time_sec = dto.time_sec;
            point_msg.asset_id = dto.asset_id;
            point_msg.position_x = dto.position_x;
            point_msg.position_y = dto.position_y;
            point_msg.position_z = dto.position_z;
            point_msg.velocity = dto.velocity;
            point_msg.is_collided = dto.is_collided;
            response->trajectory_points.push_back(point_msg);

            if (request->real_time_playback) {
                this->publish_simulation_state();
                std::this_thread::sleep_for(std::chrono::duration<double>(dt));
            }

            current_time += dt;
        }

        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::gmtime(&in_time_t), "%Y-%m-%dT%H:%M:%SZ");

        response->is_success = true;
        response->collision_count = total_collisions;
        response->estimated_cycle_time_sec = current_time;
        response->evaluated_at = ss.str();
        response->error_message = "";
    } catch (const shared::GlobalExceptionHandler& exc) {
        response->is_success = false;
        response->error_message = exc.what();
    } catch (const std::exception& exc) {
        response->is_success = false;
        response->error_message = exc.what();
    }
}

void MujocoPhysicsAdapterNode::trigger_failsafe_stop() {
    if (engine_wrapper_) {
        engine_wrapper_->freeze_and_brake();
    }
}

void MujocoPhysicsAdapterNode::on_failsafe_estop_received(const shared_interfaces::msg::FailsafeCommand& msg) {
    RCLCPP_WARN(this->get_logger(), "E-Stop received: %s (Reason: %s)", msg.action_type.c_str(), msg.trigger_reason.c_str());
    trigger_failsafe_stop();
}

void MujocoPhysicsAdapterNode::publish_simulation_state() {
    if (!engine_wrapper_ || engine_wrapper_->is_locked()) {
        return;
    }

    const mjModel* m = engine_wrapper_->get_model();
    const mjData* d = engine_wrapper_->get_data();
    if (!m || !d) {
        return;
    }

    auto now_stamp = this->now();

    std::vector<std::string> joint_names;
    joint_names.reserve(m->njnt);
    for (int i = 0; i < m->njnt; ++i) {
        const char* name = mj_id2name(m, mjOBJ_JOINT, i);
        joint_names.push_back(name ? name : ("joint_" + std::to_string(i)));
    }

    auto positions = engine_wrapper_->get_joint_positions();
    auto velocities = engine_wrapper_->get_joint_velocities();
    auto torques = engine_wrapper_->get_joint_torques();

    auto joint_state_msg = mapper_.to_ros2_joint_state(joint_names, positions, velocities, torques, now_stamp);
    joint_pub_->publish(joint_state_msg);

    auto transforms = mapper_.to_ros2_tf(m, d, base_frame_id_, tf_prefix_, now_stamp);
    for (const auto& tf_msg : transforms) {
        tf_broadcaster_->sendTransform(tf_msg);
    }
}

bool MujocoPhysicsAdapterNode::is_simulation_locked() const noexcept {
    return engine_wrapper_ ? engine_wrapper_->is_locked() : true;
}

}  // namespace sftwin::plugins::mujoco
