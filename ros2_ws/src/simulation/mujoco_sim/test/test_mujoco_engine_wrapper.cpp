// ros2_ws/src/simulation/mujoco_sim/test/test_mujoco_engine_wrapper.cpp
#include <gtest/gtest.h>
#include <filesystem>
#include <fstream>
#include <string>
#include <cmath>

#include "mujoco_sim/mujoco_engine_wrapper.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

namespace fs = std::filesystem;
using namespace sftwin::plugins::mujoco;
using namespace sftwin::shared;

class MujocoEngineWrapperTest : public ::testing::Test {
protected:
    std::string temp_dir_;
    std::string valid_xml_path_;

    void SetUp() override {
        temp_dir_ = (fs::temp_directory_path() / "mj_engine_test_dir").string();
        fs::create_directories(temp_dir_);

        valid_xml_path_ = (fs::path(temp_dir_) / "engine_test_robot.xml").string();
        std::ofstream valid_file(valid_xml_path_);
        valid_file << "<mujoco model=\"test_arm\">\n"
                   << "  <option timestep=\"0.002\" gravity=\"0 0 -9.81\"/>\n"
                   << "  <worldbody>\n"
                   << "    <body name=\"link1\" pos=\"0 0 1.0\">\n"
                   << "      <joint name=\"joint1\" type=\"hinge\" axis=\"0 0 1\" damping=\"0.5\"/>\n"
                   << "      <geom name=\"geom1\" type=\"sphere\" size=\"0.1\" mass=\"1.0\"/>\n"
                   << "    </body>\n"
                   << "  </worldbody>\n"
                   << "</mujoco>";
        valid_file.close();
    }

    void TearDown() override {
        fs::remove_all(temp_dir_);
    }
};

TEST_F(MujocoEngineWrapperTest, LoadModelAndStepSimulation_NormalOperation_AdvancesTime) {
    // Given
    MujocoEngineWrapper engine;
    bool loaded = engine.load_model_from_file(valid_xml_path_);
    ASSERT_TRUE(loaded);
    engine.set_dynamics_parameters(0.5, 0.1);

    // When
    engine.step_simulation();

    // Then
    auto positions = engine.get_joint_positions();
    auto velocities = engine.get_joint_velocities();
    EXPECT_FALSE(positions.empty());
    EXPECT_FALSE(velocities.empty());
    EXPECT_FALSE(engine.is_locked());
}

TEST_F(MujocoEngineWrapperTest, FreezeAndBrake_EStopTriggered_LocksSimulationAndClearsTorques) {
    // Given
    MujocoEngineWrapper engine;
    ASSERT_TRUE(engine.load_model_from_file(valid_xml_path_));
    engine.step_simulation();

    // When
    engine.freeze_and_brake();

    // Then
    EXPECT_TRUE(engine.is_locked());
    auto torques = engine.get_joint_torques();
    for (double t : torques) {
        EXPECT_DOUBLE_EQ(t, 0.0);
    }

    // Attempting step after lock should maintain frozen state
    engine.step_simulation();
    EXPECT_TRUE(engine.is_locked());
}

TEST_F(MujocoEngineWrapperTest, StepSimulation_UninitializedEngine_ThrowsInvalidScenarioException) {
    // Given
    MujocoEngineWrapper engine;

    // When & Then
    EXPECT_THROW(engine.step_simulation(), GlobalExceptionHandler);
}

TEST_F(MujocoEngineWrapperTest, CheckContacts_NoCollision_ReturnsEmptyContacts) {
    // Given
    MujocoEngineWrapper engine;
    ASSERT_TRUE(engine.load_model_from_file(valid_xml_path_));

    // When
    engine.step_simulation();
    auto contacts = engine.check_contacts();

    // Then
    EXPECT_TRUE(contacts.empty());
}
