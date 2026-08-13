// core/src/simulation/fms_execution/ports/i_physics_engine.hpp
#pragma once
#include <vector>
#include <string>

namespace sftwin::simulation::ports {

struct JointState {
    std::string joint_name;
    double position;
    double velocity;
    double torque;
};

class IPhysicsEnginePort {
   public:
    virtual ~IPhysicsEnginePort() = default;

    virtual bool load_model_xml(const std::string& xml_path) = 0;
    virtual void step_simulation(double dt_sec) = 0;
    virtual void set_joint_torques(const std::vector<double>& torques) = 0;
    virtual std::vector<JointState> get_joint_states() const = 0;
};

}  // namespace sftwin::simulation::ports
