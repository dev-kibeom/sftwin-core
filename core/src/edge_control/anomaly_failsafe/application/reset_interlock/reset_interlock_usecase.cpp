#include "reset_interlock_usecase.hpp"

#include <stdexcept>
#include <utility>

#include "edge_control/contracts/dtos/failsafe_command_dto.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/utils/time_provider.hpp"
#include "reset_interlock_dto.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
using namespace sftwin::shared;

ResetInterlockUseCase::ResetInterlockUseCase(
    std::shared_ptr<domain::InterlockManager> interlock_mgr,
    domain::EstopResetPolicy policy,
    std::shared_ptr<IHardwareInterlock> hw_interlock,
    std::shared_ptr<IFailsafePublisher> failsafe_pub,
    std::shared_ptr<GlobalSystemLogger> system_logger)
    : _interlock_mgr(std::move(interlock_mgr)),
      _policy(std::move(policy)),
      _hw_interlock(std::move(hw_interlock)),
      _failsafe_pub(std::move(failsafe_pub)),
      _system_logger(system_logger ? std::move(system_logger)
                                   : std::make_shared<GlobalSystemLogger>("ResetInterlockUseCase")) {}

domain::InterlockState ResetInterlockUseCase::execute(const ResetInterlockRequestDto& request_dto) {
    // 1. 도메인 2단계 리셋 정책 검증
    try {
        _policy.validate_reset_request(
            _interlock_mgr->state(),
            request_dto.is_field_inspected,
            request_dto.is_manager_approved
        );
    } catch (const std::invalid_argument& e) {
        throw GlobalExceptionHandler(
            GlobalErrorCode::ERR_EDGE_INTERLOCK_RESET_DENIED,
            e.what()
        );
    } catch (const std::logic_error& e) {
        throw GlobalExceptionHandler(
            GlobalErrorCode::ERR_COMMON_INVALID_INPUT,
            e.what()
        );
    }

    // 2. 물리 하드웨어 릴레이 차단 해제
    if (_hw_interlock) {
        _hw_interlock->release_interlock("RESET_AUTHORIZED");
    }

    // 3. 도메인 인터록 해제
    _interlock_mgr->release();

    // 4. 복구 완료 이벤트 발행
    const uint64_t current_time_ns = GlobalTimeProvider::get_steady_time_ns();
    if (_failsafe_pub) {
        FailsafeCommandDto cmd(request_dto.device_id, "RESUME", "MANUAL_2STEP_RESET_SUCCESS", current_time_ns);
        _failsafe_pub->publish("failsafe/resume", cmd);
    }

    _system_logger->info("E-Stop Interlock successfully released for device: {}. State -> RELEASED",
                    request_dto.device_id);
    return domain::InterlockState::RELEASED;
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
