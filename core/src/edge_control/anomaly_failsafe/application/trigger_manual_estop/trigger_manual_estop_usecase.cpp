#include "trigger_manual_estop_usecase.hpp"

#include <utility>

#include "edge_control/contracts/dtos/failsafe_command_dto.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/utils/time_provider.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
using namespace sftwin::shared;

TriggerManualEstopUseCase::TriggerManualEstopUseCase(
    std::shared_ptr<domain::InterlockManager> interlock_mgr,
    std::shared_ptr<IHardwareInterlock> hw_interlock,
    std::shared_ptr<IFailsafePublisher> failsafe_pub,
    std::shared_ptr<GlobalSystemLogger> system_logger)
    : _interlock_mgr(std::move(interlock_mgr)),
      _hw_interlock(std::move(hw_interlock)),
      _failsafe_pub(std::move(failsafe_pub)),
      _system_logger(system_logger ? std::move(system_logger)
                                   : std::make_shared<GlobalSystemLogger>("TriggerManualEstopUseCase")) {}

void TriggerManualEstopUseCase::execute(const TriggerManualEstopRequestDto& request_dto) {
    // 1. 현재 인터록 상태 검증 (이미 정지 또는 복구 중이면 예외 발생)
    if (_interlock_mgr->state() != domain::InterlockState::RELEASED) {
        _system_logger->warn("Invalid state transition: E-Stop requested but interlock is not RELEASED.");
        throw GlobalExceptionHandler(
            GlobalErrorCode::ERR_COMMON_INVALID_INPUT,
            "Engine is already interlocked or in recovery."
        );
    }

    // 2. 물리 하드웨어 릴레이 차단
    if (_hw_interlock) {
        _hw_interlock->trigger_physical_relay();
    }

    // 3. E-Stop 명령 발행 (외부 관제/필드 전파)
    const uint64_t current_time_ns = GlobalTimeProvider::get_steady_time_ns();
    if (_failsafe_pub) {
        _failsafe_pub->publish(
            "failsafe/estop",
            FailsafeCommandDto(request_dto.device_id, "ESTOP", request_dto.reason, current_time_ns)
        );
    }

    // 4. 도메인 상태 전이
    _interlock_mgr->engage_estop();

    _system_logger->info("Manual E-Stop successfully triggered. Device: {}, Reason: {}",
                    request_dto.device_id, request_dto.reason);
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
