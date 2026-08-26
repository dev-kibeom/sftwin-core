// ros2_ws/src/simulation/mujoco_sim/include/mujoco_sim/mujoco_data_mapper.hpp
#pragma once

#include <string>
#include <vector>
#include <cmath>
#include <mujoco/mujoco.h>
#include <rclcpp/time.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>

namespace sftwin::plugins::mujoco {

struct TrajectoryPointDto {
    double time_sec{0.0};
    std::string asset_id;
    double position_x{0.0};
    double position_y{0.0};
    double position_z{0.0};
    double velocity{0.0};
    bool is_collided{false};
};

class MujocoDataMapper {
public:
    MujocoDataMapper() = default;
    ~MujocoDataMapper() = default;

    TrajectoryPointDto to_trajectory_point(
        const mjData* d,
        double time_sec,
        const std::string& asset_id,
        bool is_collided
    ) const;

    sensor_msgs::msg::JointState to_ros2_joint_state(
        const std::vector<std::string>& joint_names,
        const std::vector<double>& positions,
        const std::vector<double>& velocities,
        const std::vector<double>& efforts,
        const rclcpp::Time& stamp
    ) const;

    std::vector<geometry_msgs::msg::TransformStamped> to_ros2_tf(
        const mjModel* m,
        const mjData* d,
        const std::string& base_frame_id,
        const std::string& tf_prefix,
        const rclcpp::Time& stamp
    ) const;
};

}  // namespace sftwin::plugins::mujoco
