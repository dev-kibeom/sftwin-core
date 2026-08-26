// ros2_ws/src/simulation/mujoco_sim/include/mujoco_sim/mujoco_engine_wrapper.hpp
#pragma once

#include <atomic>
#include <memory>
#include <mutex>
#include <string>
#include <vector>
#include <mujoco/mujoco.h>

#include "mujoco_sim/mjcf_model_loader.hpp"

namespace sftwin::plugins::mujoco {

struct ContactInfo {
    int geom1_id{-1};
    int geom2_id{-1};
    double distance{0.0};
    bool is_collided{false};
};

class MujocoEngineWrapper {
public:
    MujocoEngineWrapper();
    ~MujocoEngineWrapper() = default;

    bool load_model_from_file(const std::string& xml_path);
    void set_dynamics_parameters(double damping, double friction);
    void step_simulation();
    void freeze_and_brake();
    void reset();

    std::vector<double> get_joint_positions();
    std::vector<double> get_joint_velocities();
    std::vector<double> get_joint_torques();
    std::vector<ContactInfo> check_contacts();

    bool is_locked() const noexcept;
    const mjModel* get_model() const noexcept;
    const mjData* get_data() const noexcept;

private:
    UniqueMjModel model_;
    UniqueMjData data_;
    std::atomic<bool> is_locked_{false};
    double dt_{0.002};
    std::mutex mutex_;
};

}  // namespace sftwin::plugins::mujoco
