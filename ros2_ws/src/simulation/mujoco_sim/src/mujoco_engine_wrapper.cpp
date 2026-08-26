// ros2_ws/src/simulation/mujoco_sim/src/mujoco_engine_wrapper.cpp
#include "mujoco_sim/mujoco_engine_wrapper.hpp"
#include <cmath>
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"

namespace sftwin::plugins::mujoco {

MujocoEngineWrapper::MujocoEngineWrapper() = default;

bool MujocoEngineWrapper::load_model_from_file(const std::string& xml_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    MjcfModelLoader loader;
    model_ = loader.load_mjmodel(xml_path);

    if (!model_) {
        return false;
    }

    mjData* raw_data = mj_makeData(model_.get());
    data_ = UniqueMjData(raw_data);
    is_locked_.store(false);

    if (model_->opt.timestep > 0.0) {
        dt_ = model_->opt.timestep;
    }

    mj_forward(model_.get(), data_.get());
    return true;
}

void MujocoEngineWrapper::set_dynamics_parameters(double damping, double friction) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!model_) {
        return;
    }

    for (int i = 0; i < model_->nv; ++i) {
        model_->dof_damping[i] = damping;
        model_->dof_frictionloss[i] = friction;
    }
}

void MujocoEngineWrapper::step_simulation() {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!model_ || !data_) {
        throw shared::GlobalExceptionHandler(
            shared::GlobalErrorCode::ERR_SIM_INVALID_SCENARIO,
            "MuJoCo engine is not initialized. Call load_model_from_file first."
        );
    }

    if (is_locked_.load()) {
        return;
    }

    mj_step(model_.get(), data_.get());

    for (int i = 0; i < model_->nv; ++i) {
        if (std::isnan(data_->qpos[i]) || std::isinf(data_->qpos[i]) ||
            std::isnan(data_->qvel[i]) || std::isinf(data_->qvel[i])) {
            throw shared::GlobalExceptionHandler(
                shared::GlobalErrorCode::ERR_SIM_RESOURCE_EXHAUSTED,
                "Physics simulation diverged (NaN/Inf detected in state values)."
            );
        }
    }
}

void MujocoEngineWrapper::freeze_and_brake() {
    std::lock_guard<std::mutex> lock(mutex_);
    is_locked_.store(true);

    if (data_ && model_) {
        for (int i = 0; i < model_->nv; ++i) {
            data_->qfrc_applied[i] = 0.0;
            data_->qvel[i] = 0.0;
        }
    }
}

void MujocoEngineWrapper::reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (model_ && data_) {
        mj_resetData(model_.get(), data_.get());
        is_locked_.store(false);
        mj_forward(model_.get(), data_.get());
    }
}

std::vector<double> MujocoEngineWrapper::get_joint_positions() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!model_ || !data_) {
        return {};
    }
    return std::vector<double>(data_->qpos, data_->qpos + model_->nq);
}

std::vector<double> MujocoEngineWrapper::get_joint_velocities() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!model_ || !data_) {
        return {};
    }
    return std::vector<double>(data_->qvel, data_->qvel + model_->nv);
}

std::vector<double> MujocoEngineWrapper::get_joint_torques() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!model_ || !data_) {
        return {};
    }
    return std::vector<double>(data_->qfrc_applied, data_->qfrc_applied + model_->nv);
}

std::vector<ContactInfo> MujocoEngineWrapper::check_contacts() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!data_ || !model_) {
        return {};
    }

    std::vector<ContactInfo> contacts;
    for (int i = 0; i < data_->ncon; ++i) {
        const auto& c = data_->contact[i];
        bool collided = (c.dist <= 0.001);
        contacts.push_back({c.geom1, c.geom2, c.dist, collided});
    }
    return contacts;
}

bool MujocoEngineWrapper::is_locked() const noexcept {
    return is_locked_.load();
}

const mjModel* MujocoEngineWrapper::get_model() const noexcept {
    return model_.get();
}

const mjData* MujocoEngineWrapper::get_data() const noexcept {
    return data_.get();
}

}  // namespace sftwin::plugins::mujoco
