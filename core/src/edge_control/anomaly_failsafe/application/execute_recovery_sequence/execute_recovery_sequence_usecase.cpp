#include "execute_recovery_sequence_usecase.hpp"

#include <utility>

#include "edge_control/contracts/dtos/failsafe_command_dto.hpp"
#include "shared/exceptions/global_error_code_enum.hpp"
#include "shared/exceptions/global_exception_handler.hpp"
#include "shared/utils/time_provider.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {
using namespace sftwin::shared;

ExecuteRecoverySequenceUseCase::ExecuteRecoverySequenceUseCase(
    std::shared_ptr<domain::InterlockManager> interlock_mgr,
    std::shared_ptr<IFailsafePublisher> failsafe_pub,
    std::shared_ptr<IRecoverySequence> recovery,
    std::shared_ptr<GlobalSystemLogger> system_logger)
    : _interlock_mgr(std::move(interlock_mgr)),
      _failsafe_pub(std::move(failsafe_pub)),
      _recovery(std::move(recovery)),
      _system_logger(system_logger ? std::move(system_logger)
                                   : std::make_shared<GlobalSystemLogger>("ExecuteRecoverySequenceUseCase")) {}

RecoveryExecutionResultDto ExecuteRecoverySequenceUseCase::execute(
    const ExecuteRecoverySequenceRequestDto& request_dto) {
    // 1. 현재 인터록 상태 검증 (ENGAGED 상태일 때만 복구 시도 가능)
    if (_interlock_mgr->state() != domain::InterlockState::ENGAGED) {
        _system_logger->warn("Invalid state transition: Recovery requested but engine is not ENGAGED.");
        throw GlobalExceptionHandler(
            GlobalErrorCode::ERR_COMMON_INVALID_INPUT,
            "Engine is not in an interlocked state."
        );
    }

    // 2. 도메인 상태 전이 (복구 승인 대기 상태)
    _interlock_mgr->start_recovery();
    _system_logger->info("Recovery sequence started for device: {}. State -> PENDING_RESET_APPROVAL",
                    request_dto.device_id);

    // 3. 복구 시퀀스 포트 실행
    if (!_recovery) {
        _interlock_mgr->cancel_recovery();
        return RecoveryExecutionResultDto::failure(
            "Recovery port is null.",
            "ERR_COMMON_INTERNAL_ERROR"
        );
    }

    const auto result = _recovery->execute_sequence(request_dto.sequence_script);
    if (!result.is_success()) {
        _system_logger->error("Recovery sequence execution failed for device: {}. Message: {}",
                         request_dto.device_id, result.error_message());
        _interlock_mgr->cancel_recovery();
        return result;
    }

    // 4. 복구 성공 시 인터록 해제 및 RESUME 이벤트 발행
    _interlock_mgr->release();

    const uint64_t current_time_ns = GlobalTimeProvider::get_steady_time_ns();
    if (_failsafe_pub) {
        _failsafe_pub->publish(
            "failsafe/resume",
            FailsafeCommandDto(request_dto.device_id, "RESUME", "RECOVERY_SUCCESS", current_time_ns)
        );
    }

    _system_logger->info("Recovery completed successfully for device: {}. State -> RELEASED",
                    request_dto.device_id);
    return RecoveryExecutionResultDto::success();
}

}  // namespace sftwin::edge_control::anomaly_failsafe::application
