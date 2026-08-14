#include "src/edge_control/anomaly_failsafe/application/reset_estop_interlock/reset_estop_interlock_usecase.hpp"
#include "src/edge_control/common/logging/edge_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

domain::EdgeEngineState ResetEstopInterlockUseCase::execute(domain::EdgeEngineState current_state,
                                                     bool is_field_inspected,
                                                     bool is_manager_approved) {
    EDGE_LOG_INFO("E-Stop 2-Step Reset requested for device: {}", _edge_device_id);

    // 1. 도메인 정책 규칙 검증
    _policy.validate_reset_request(current_state, is_field_inspected, is_manager_approved);

    // 2. 통신망에 안전 해제 명령 발행
    //    C++11/17 std::move를 통해 DTO 임시 객체를 복사 없이 publisher로 소유권 이동
    _failsafe_pub->publish(
        "failsafe/resume",
        FailsafeCommandDto(_edge_device_id, "RESUME", "MANUAL_2STEP_RESET_SUCCESS")
    );

    EDGE_LOG_INFO("E-Stop Interlock successfully released. Engine state -> ACTIVE_MONITORING");

    return domain::EdgeEngineState::ACTIVE_MONITORING;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
