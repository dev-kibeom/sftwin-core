// ros2_ws/src/simulation/mujoco_sim/include/mujoco_sim/mjcf_model_loader.hpp
#pragma once

#include <filesystem>
#include <memory>
#include <string>
#include <mujoco/mujoco.h>

namespace sftwin::plugins::mujoco
{

struct MjModelDeleter
{
  void operator()(mjModel * m) const noexcept
  {
    if (m != nullptr) {
      mj_deleteModel(m);
    }
  }
};

struct MjDataDeleter
{
  void operator()(mjData * d) const noexcept
  {
    if (d != nullptr) {
      mj_deleteData(d);
    }
  }
};

using UniqueMjModel = std::unique_ptr<mjModel, MjModelDeleter>;
using UniqueMjData = std::unique_ptr<mjData, MjDataDeleter>;

class MjcfModelLoader
{
public:
  MjcfModelLoader() = default;
  ~MjcfModelLoader() = default;

  UniqueMjModel load_mjmodel(const std::string & xml_path);
  bool validate_kinematics(const mjModel * m, int required_dof) const noexcept;
};

}  // namespace sftwin::plugins::mujoco
