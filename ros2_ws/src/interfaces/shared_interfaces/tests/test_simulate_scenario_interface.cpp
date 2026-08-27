// ros2_ws/src/interfaces/shared_interfaces/tests/test_simulate_scenario_interface.cpp
#include <gtest/gtest.h>
#include <string>
#include <vector>
#include "geometry_msgs/msg/pose.hpp"
#include "shared_interfaces/srv/simulate_scenario.hpp"

using SimulateScenario = shared_interfaces::srv::SimulateScenario;

TEST(SimulateScenarioInterfaceTest, RequestInstantiation_SeparatedWaypointsAndPlayback_SetsFieldsCorrectly) {
    // Given
    SimulateScenario::Request request;
    request.scenario_id = "SCENARIO_EXP_001";
    request.baseline_id = "BASELINE_EXP_001";
    request.model_file_path = "/path/to/robot_scene.xml";
    request.dt_sec = 0.002;
    request.max_duration_sec = 5.0;
    request.joint_damping = 0.8;
    request.friction_loss = 0.2;
    request.real_time_playback = true;

    geometry_msgs::msg::Pose nav_pose;
    nav_pose.position.x = 1.0;
    nav_pose.position.y = 2.0;
    nav_pose.position.z = 0.0;
    nav_pose.orientation.w = 1.0;

    geometry_msgs::msg::Pose arm_pose;
    arm_pose.position.x = 0.5;
    arm_pose.position.y = 0.0;
    arm_pose.position.z = 0.8;
    arm_pose.orientation.w = 0.707;
    arm_pose.orientation.z = 0.707;

    // When
    request.nav_waypoints.push_back(nav_pose);
    request.arm_target_poses.push_back(arm_pose);

    // Then
    EXPECT_EQ(request.scenario_id, "SCENARIO_EXP_001");
    EXPECT_TRUE(request.real_time_playback);
    ASSERT_EQ(request.nav_waypoints.size(), 1);
    EXPECT_DOUBLE_EQ(request.nav_waypoints[0].position.x, 1.0);
    EXPECT_DOUBLE_EQ(request.nav_waypoints[0].position.y, 2.0);
    EXPECT_DOUBLE_EQ(request.nav_waypoints[0].orientation.w, 1.0);

    ASSERT_EQ(request.arm_target_poses.size(), 1);
    EXPECT_DOUBLE_EQ(request.arm_target_poses[0].position.x, 0.5);
    EXPECT_DOUBLE_EQ(request.arm_target_poses[0].position.z, 0.8);
    EXPECT_DOUBLE_EQ(request.arm_target_poses[0].orientation.w, 0.707);
}

TEST(SimulateScenarioInterfaceTest, ResponseInstantiation_StandardFields_SetsFieldsCorrectly) {
    // Given
    SimulateScenario::Response response;
    response.is_success = true;
    response.collision_count = 0;
    response.estimated_cycle_time_sec = 4.85;
    response.evaluated_at = "2026-08-27T01:19:00Z";
    response.error_message = "";

    shared_interfaces::msg::TrajectoryPoint point;
    point.time_sec = 0.002;
    point.asset_id = "ROBOT_01";
    point.position_x = 0.0;
    point.position_y = 0.0;
    point.position_z = 0.0;
    point.velocity = 0.0;
    point.is_collided = false;

    // When
    response.trajectory_points.push_back(point);

    // Then
    EXPECT_TRUE(response.is_success);
    EXPECT_EQ(response.collision_count, 0);
    EXPECT_DOUBLE_EQ(response.estimated_cycle_time_sec, 4.85);
    ASSERT_EQ(response.trajectory_points.size(), 1);
    EXPECT_EQ(response.trajectory_points[0].asset_id, "ROBOT_01");
}
