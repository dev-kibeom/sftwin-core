// ros2_ws/src/simulation/mujoco_sim/test/test_mujoco_data_mapper.cpp
#include <gtest/gtest.h>
#include <vector>
#include <string>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <mujoco/mujoco.h>
#include <rclcpp/time.hpp>

#include "mujoco_sim/mujoco_data_mapper.hpp"
#include "mujoco_sim/mjcf_model_loader.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

namespace fs = std::filesystem;
using namespace sftwin::plugins::mujoco;
using namespace sftwin::shared;

class MujocoDataMapperTest : public ::testing::Test {
protected:
    std::string temp_dir_;
    std::string valid_xml_path_;
    UniqueMjModel model_;
    UniqueMjData data_;

    void SetUp() override {
        temp_dir_ = (fs::temp_directory_path() / "mj_data_mapper_test_dir").string();
        fs::create_directories(temp_dir_);

        valid_xml_path_ = (fs::path(temp_dir_) / "mapper_test_robot.xml").string();
        std::ofstream valid_file(valid_xml_path_);
        valid_file << "<mujoco model=\"test_robot\">\n"
                   << "  <worldbody>\n"
                   << "    <body name=\"link1\" pos=\"1.0 2.0 3.0\">\n"
                   << "      <joint name=\"joint1\" type=\"hinge\" axis=\"0 0 1\"/>\n"
                   << "      <geom type=\"sphere\" size=\"0.1\"/>\n"
                   << "    </body>\n"
                   << "  </worldbody>\n"
                   << "</mujoco>";
        valid_file.close();

        MjcfModelLoader loader;
        model_ = loader.load_mjmodel(valid_xml_path_);
        if (model_) {
            data_ = UniqueMjData(mj_makeData(model_.get()));
            mj_forward(model_.get(), data_.get());
        }
    }

    void TearDown() override {
        fs::remove_all(temp_dir_);
    }
};

TEST_F(MujocoDataMapperTest, ToTrajectoryPoint_ValidInputs_ReturnsMappedDtoWith3DPosition) {
    // Given
    MujocoDataMapper mapper;
    ASSERT_NE(model_, nullptr);
    ASSERT_NE(data_, nullptr);
    data_->time = 1.25;
    data_->qpos[0] = 0.5;
    data_->qvel[0] = 1.5;
    std::string asset_id = "ROBOT_01";
    bool is_collided = false;

    // When (Updated signature: model_, data_, ...)
    auto dto = mapper.to_trajectory_point(model_.get(), data_.get(), 1.25, asset_id, is_collided);

    // Then
    EXPECT_DOUBLE_EQ(dto.time_sec, 1.25);
    EXPECT_EQ(dto.asset_id, "ROBOT_01");
    EXPECT_FALSE(dto.is_collided);
    EXPECT_DOUBLE_EQ(dto.position_x, 1.0);
    EXPECT_DOUBLE_EQ(dto.position_y, 2.0);
    EXPECT_DOUBLE_EQ(dto.position_z, 3.0);
    EXPECT_NEAR(dto.velocity, 1.5, 1e-4);
}

TEST_F(MujocoDataMapperTest, ToRos2JointState_ValidInputs_ReturnsSerializedJointState) {
    // Given
    MujocoDataMapper mapper;
    std::vector<std::string> joint_names = {"joint1"};
    std::vector<double> positions = {0.785};
    std::vector<double> velocities = {0.1};
    std::vector<double> efforts = {15.0};
    rclcpp::Time stamp(100, 0);

    // When
    auto joint_state_msg = mapper.to_ros2_joint_state(joint_names, positions, velocities, efforts, stamp);

    // Then
    EXPECT_EQ(joint_state_msg.name.size(), 1);
    EXPECT_EQ(joint_state_msg.name[0], "joint1");
    EXPECT_DOUBLE_EQ(joint_state_msg.position[0], 0.785);
    EXPECT_DOUBLE_EQ(joint_state_msg.velocity[0], 0.1);
    EXPECT_DOUBLE_EQ(joint_state_msg.effort[0], 15.0);
}

TEST_F(MujocoDataMapperTest, ToRos2Tf_ValidModelAndData_ReturnsTransformArray) {
    // Given
    MujocoDataMapper mapper;
    ASSERT_NE(model_, nullptr);
    ASSERT_NE(data_, nullptr);
    rclcpp::Time stamp(50, 0);
    std::string base_frame = "world";
    std::string tf_prefix = "sftwin_";

    // When
    auto transforms = mapper.to_ros2_tf(model_.get(), data_.get(), base_frame, tf_prefix, stamp);

    // Then
    EXPECT_GE(transforms.size(), 1);
    EXPECT_EQ(transforms[0].header.frame_id, "world");
    EXPECT_EQ(transforms[0].child_frame_id, "sftwin_link1");
    EXPECT_DOUBLE_EQ(transforms[0].transform.translation.x, 1.0);
    EXPECT_DOUBLE_EQ(transforms[0].transform.translation.y, 2.0);
    EXPECT_DOUBLE_EQ(transforms[0].transform.translation.z, 3.0);
}

TEST_F(MujocoDataMapperTest, ToTrajectoryPoint_NullData_ThrowsInvalidInputException) {
    // Given
    MujocoDataMapper mapper;

    // When & Then
    EXPECT_THROW(
        mapper.to_trajectory_point(model_.get(), nullptr, 0.0, "ROBOT_01", false),
        GlobalExceptionHandler
    );
}

TEST_F(MujocoDataMapperTest, ToRos2Tf_NullModelOrData_ThrowsInvalidInputException) {
    // Given
    MujocoDataMapper mapper;
    rclcpp::Time stamp(0, 0);

    // When & Then
    EXPECT_THROW(
        mapper.to_ros2_tf(nullptr, data_.get(), "world", "sftwin_", stamp),
        GlobalExceptionHandler
    );
    EXPECT_THROW(
        mapper.to_ros2_tf(model_.get(), nullptr, "world", "sftwin_", stamp),
        GlobalExceptionHandler
    );
}
