// ros2_ws/src/simulation/mujoco_sim/src/mujoco_data_mapper.cpp
#include "mujoco_sim/mujoco_data_mapper.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

namespace sftwin::plugins::mujoco {

TrajectoryPointDto MujocoDataMapper::to_trajectory_point(
    const mjData* d,
    double time_sec,
    const std::string& asset_id,
    bool is_collided
) const {
    if (d == nullptr) {
        throw shared::GlobalExceptionHandler(
            shared::GlobalErrorCode::ERR_COMMON_INVALID_INPUT,
            "mjData pointer is null while mapping to TrajectoryPointDto."
        );
    }

    TrajectoryPointDto dto;
    dto.time_sec = time_sec;
    dto.asset_id = asset_id;
    dto.is_collided = is_collided;

    if (d->qpos != nullptr) {
        dto.position_x = d->qpos[0];
    }
    if (d->qvel != nullptr) {
        dto.velocity = std::abs(d->qvel[0]);
    }

    return dto;
}

sensor_msgs::msg::JointState MujocoDataMapper::to_ros2_joint_state(
    const std::vector<std::string>& joint_names,
    const std::vector<double>& positions,
    const std::vector<double>& velocities,
    const std::vector<double>& efforts,
    const rclcpp::Time& stamp
) const {
    sensor_msgs::msg::JointState msg;
    msg.header.stamp = stamp;
    msg.name = joint_names;
    msg.position = positions;
    msg.velocity = velocities;
    msg.effort = efforts;
    return msg;
}

std::vector<geometry_msgs::msg::TransformStamped> MujocoDataMapper::to_ros2_tf(
    const mjModel* m,
    const mjData* d,
    const std::string& base_frame_id,
    const std::string& tf_prefix,
    const rclcpp::Time& stamp
) const {
    if (m == nullptr || d == nullptr) {
        throw shared::GlobalExceptionHandler(
            shared::GlobalErrorCode::ERR_COMMON_INVALID_INPUT,
            "mjModel or mjData pointer is null while mapping to ROS 2 TF."
        );
    }

    std::vector<geometry_msgs::msg::TransformStamped> transforms;
    transforms.reserve(m->nbody > 1 ? m->nbody - 1 : 0);

    for (int body_id = 1; body_id < m->nbody; ++body_id) {
        geometry_msgs::msg::TransformStamped tf_msg;
        tf_msg.header.stamp = stamp;
        tf_msg.header.frame_id = base_frame_id;

        const char* body_name = mj_id2name(m, mjOBJ_BODY, body_id);
        std::string name_str = (body_name != nullptr) ? body_name : ("body_" + std::to_string(body_id));
        tf_msg.child_frame_id = tf_prefix + name_str;

        tf_msg.transform.translation.x = d->xpos[3 * body_id + 0];
        tf_msg.transform.translation.y = d->xpos[3 * body_id + 1];
        tf_msg.transform.translation.z = d->xpos[3 * body_id + 2];

        tf_msg.transform.rotation.w = d->xquat[4 * body_id + 0];
        tf_msg.transform.rotation.x = d->xquat[4 * body_id + 1];
        tf_msg.transform.rotation.y = d->xquat[4 * body_id + 2];
        tf_msg.transform.rotation.z = d->xquat[4 * body_id + 3];

        transforms.push_back(std::move(tf_msg));
    }

    return transforms;
}

}  // namespace sftwin::plugins::mujoco
