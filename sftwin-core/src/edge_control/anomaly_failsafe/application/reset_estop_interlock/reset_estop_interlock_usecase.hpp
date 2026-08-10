#pragma once
#include <memory>
#include <string>

#include "src/edge_control/anomaly_failsafe/adapters/failsafe_protobuf_mapper.hpp"
#include "src/edge_control/anomaly_failsafe/domain/edge_local_enums.hpp"
#include "src/edge_control/anomaly_failsafe/domain/estop_reset_policy.hpp"
#include "src/edge_control/anomaly_failsafe/ports/i_failsafe_publisher.hpp"
#include "src/edge_control/anomaly_failsafe/ports/i_hardware_interlock.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class ResetEstopInterlockUseCase {
   private:
    std::shared_ptr<ports::IHardwareInterlock> _hw_interlock;
    std::shared_ptr<ports::IFailsafePublisher> _dds_pub;
    std::shared_ptr<adapters::FailsafeProtobufMapper> _mapper;
    domain::EstopResetPolicy _policy;
    std::string _edge_device_id;

   public:
    ResetEstopInterlockUseCase(std::shared_ptr<ports::IHardwareInterlock> hw_interlock,
                               std::shared_ptr<ports::IFailsafePublisher> dds_pub,
                               std::shared_ptr<adapters::FailsafeProtobufMapper> mapper)
        : _hw_interlock(std::move(hw_interlock)),
          _dds_pub(std::move(dds_pub)),
          _mapper(std::move(mapper)),
          _edge_device_id("EDGE_NODE_001") {}

    domain::EdgeEngineState execute(domain::EdgeEngineState current_state, bool is_field_inspected,
                                    bool is_manager_approved);
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
