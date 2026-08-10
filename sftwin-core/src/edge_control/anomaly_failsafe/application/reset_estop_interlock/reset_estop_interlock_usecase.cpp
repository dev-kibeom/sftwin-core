#include "reset_estop_interlock_usecase.hpp"

#include "src/edge_control/common/logging/edge_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

domain::EdgeEngineState ResetEstopInterlockUseCase::execute(domain::EdgeEngineState current_state,
                                                            bool is_field_inspected,
                                                            bool is_manager_approved) {
    EDGE_LOG_INFO("E-Stop 2-Step Reset requested.");

    // 1. 도메인 정책 규칙 검증
    _policy.validate_reset_request(current_state, is_field_inspected, is_manager_approved);

    // 2. DDS 통신망에 안전 해제(RESUME/RESET) 명령 브로드캐스트
    auto proto_msg = _mapper->to_protobuf(domain::FailsafeActionEnum::RESUME, _edge_device_id,
                                          "MANUAL_2STEP_RESET_SUCCESS");
    _dds_pub->publish("failsafe/resume", dtos::FailsafeCommandDto(_edge_device_id, "RESUME",
                                                                  "MANUAL_2STEP_RESET_SUCCESS",
                                                                  proto_msg.issued_timestamp_ns()));

    EDGE_LOG_INFO("E-Stop Interlock successfully released. Engine state -> ACTIVE_MONITORING");
    return domain::EdgeEngineState::ACTIVE_MONITORING;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
