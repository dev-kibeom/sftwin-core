#pragma once
#include <memory>
#include <string>

#include "src/edge_control/anomaly_failsafe/adapters/failsafe_protobuf_mapper.hpp"
#include "src/edge_control/anomaly_failsafe/domain/edge_local_enums.hpp"
#include "src/edge_control/anomaly_failsafe/domain/failsafe_controller.hpp"
#include "src/edge_control/anomaly_failsafe/ports/i_behavior_tree_engine.hpp"
#include "src/edge_control/anomaly_failsafe/ports/i_failsafe_publisher.hpp"
#include "src/edge_control/anomaly_failsafe/ports/i_hardware_interlock.hpp"
#include "src/edge_control/realtime_telemetry/dtos/telemetry_packet_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class TriggerFailsafeUseCase {
   private:
    std::shared_ptr<ports::IHardwareInterlock> _hw_interlock;
    std::shared_ptr<ports::IFailsafePublisher> _dds_pub;
    std::shared_ptr<ports::IBehaviorTreeEngine> _bt_engine;
    std::shared_ptr<adapters::FailsafeProtobufMapper> _mapper;

    domain::FailsafeController _controller;  // EDG-002 규칙 엔진
    domain::EdgeEngineState _current_state;  // EDG-003 상태 관리자
    std::string _edge_device_id;

   public:
    TriggerFailsafeUseCase(std::shared_ptr<ports::IHardwareInterlock> hw_interlock,
                           std::shared_ptr<ports::IFailsafePublisher> dds_pub,
                           std::shared_ptr<ports::IBehaviorTreeEngine> bt_engine,
                           std::shared_ptr<adapters::FailsafeProtobufMapper> mapper,
                           const domain::FailsafeRule& rule);

    // EDG-002: 실시간 텔레메트리 기반 이상 감지 (100ms Loop)
    void evaluate_and_trigger(const sftwin::edge_control::dtos::TelemetryPacketDto& telemetry);

    // EDG-003: 수동 제어 및 복구
    void trigger_manual_estop(const std::string& reason);
    bool execute_behavior_tree_recovery(const std::string& script);

    domain::EdgeEngineState get_current_state() const { return _current_state; }
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application