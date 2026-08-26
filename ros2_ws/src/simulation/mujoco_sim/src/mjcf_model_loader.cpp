// ros2_ws/src/simulation/mujoco_sim/src/mjcf_model_loader.cpp
#include "mujoco_sim/mjcf_model_loader.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

namespace sftwin::plugins::mujoco
{

UniqueMjModel MjcfModelLoader::load_mjmodel(const std::string & xml_path)
{
  if (!std::filesystem::exists(xml_path)) {
    throw shared::GlobalExceptionHandler(
            shared::GlobalErrorCode::ERR_SIM_INVALID_SCENARIO,
            "MJCF file not found at path: " + xml_path
    );
  }

  char error_buffer[1024] = {0};
  mjModel * raw_model = mj_loadXML(xml_path.c_str(), nullptr, error_buffer, sizeof(error_buffer));

  if (raw_model == nullptr || error_buffer[0] != '\0') {
    if (raw_model != nullptr) {
      mj_deleteModel(raw_model);
    }
    std::string detailed_err = (error_buffer[0] != '\0') ? error_buffer : "Unknown parsing error";
    throw shared::GlobalExceptionHandler(
            shared::GlobalErrorCode::ERR_SIM_INVALID_SCENARIO,
            "Failed to parse MJCF XML (" + xml_path + "): " + detailed_err
    );
  }

  return UniqueMjModel(raw_model);
}

bool MjcfModelLoader::validate_kinematics(const mjModel * m, int required_dof) const noexcept
{
  if (m == nullptr) {
    return false;
  }
  return m->nq == required_dof || m->nv == required_dof;
}

}  // namespace sftwin::plugins::mujoco
