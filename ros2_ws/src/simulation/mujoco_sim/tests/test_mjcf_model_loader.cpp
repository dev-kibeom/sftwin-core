// ros2_ws/src/simulation/mujoco_sim/test/test_mjcf_model_loader.cpp
#include <gtest/gtest.h>
#include <filesystem>
#include <fstream>
#include <string>

#include "mujoco_sim/mjcf_model_loader.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

namespace fs = std::filesystem;
using namespace sftwin::plugins::mujoco;
using namespace sftwin::shared;

class MjcfModelLoaderTest : public ::testing::Test
{
protected:
  std::string temp_dir_;
  std::string valid_xml_path_;
  std::string invalid_xml_path_;
  std::string non_existent_path_;

  void SetUp() override
  {
    temp_dir_ = (fs::temp_directory_path() / "mjcf_test_dir").string();
    fs::create_directories(temp_dir_);

    valid_xml_path_ = (fs::path(temp_dir_) / "valid_model.xml").string();
    std::ofstream valid_file(valid_xml_path_);
    valid_file << "<mujoco model=\"test_robot\">\n"
               << "  <worldbody>\n"
               << "    <body name=\"link1\" pos=\"0 0 0\">\n"
               << "      <joint name=\"joint1\" type=\"hinge\" axis=\"0 0 1\"/>\n"
               << "      <geom type=\"cylinder\" size=\"0.05 0.2\"/>\n"
               << "    </body>\n"
               << "  </worldbody>\n"
               << "</mujoco>";
    valid_file.close();

    invalid_xml_path_ = (fs::path(temp_dir_) / "invalid_model.xml").string();
    std::ofstream invalid_file(invalid_xml_path_);
    invalid_file << "<mujoco model=\"broken_robot\">\n"
                 << "  <worldbody>\n"
                 << "    <body name=\"link1\" pos=\"0 0 0\">\n"
                 << "      <unclosed_tag>\n"
                 << "</mujoco>";
    invalid_file.close();

    non_existent_path_ = (fs::path(temp_dir_) / "does_not_exist.xml").string();
  }

  void TearDown() override
  {
    fs::remove_all(temp_dir_);
  }
};

TEST_F(MjcfModelLoaderTest, LoadMjModel_ValidXml_ReturnsValidModelPointer) {
  // Given
  MjcfModelLoader loader;

  // When
  UniqueMjModel model = loader.load_mjmodel(valid_xml_path_);

  // Then
  ASSERT_NE(model, nullptr);
  EXPECT_GT(model->nq, 0);
  EXPECT_GT(model->nv, 0);
}

TEST_F(MjcfModelLoaderTest, LoadMjModel_NonExistentFile_ThrowsInvalidScenarioException) {
  // Given
  MjcfModelLoader loader;

  // When & Then
  EXPECT_THROW(loader.load_mjmodel(non_existent_path_), GlobalExceptionHandler);
}

TEST_F(MjcfModelLoaderTest, LoadMjModel_InvalidXmlSyntax_ThrowsInvalidScenarioException) {
  // Given
  MjcfModelLoader loader;

  // When & Then
  EXPECT_THROW(loader.load_mjmodel(invalid_xml_path_), GlobalExceptionHandler);
}

TEST_F(MjcfModelLoaderTest, ValidateKinematics_MatchesDof_ReturnsTrue) {
  // Given
  MjcfModelLoader loader;
  UniqueMjModel model = loader.load_mjmodel(valid_xml_path_);
  ASSERT_NE(model, nullptr);

  // When
  bool is_valid = loader.validate_kinematics(model.get(), 1);

  // Then
  EXPECT_TRUE(is_valid);
}

TEST_F(MjcfModelLoaderTest, ValidateKinematics_MismatchedDof_ReturnsFalse) {
  // Given
  MjcfModelLoader loader;
  UniqueMjModel model = loader.load_mjmodel(valid_xml_path_);
  ASSERT_NE(model, nullptr);

  // When
  bool is_valid = loader.validate_kinematics(model.get(), 6);

  // Then
  EXPECT_FALSE(is_valid);
}
