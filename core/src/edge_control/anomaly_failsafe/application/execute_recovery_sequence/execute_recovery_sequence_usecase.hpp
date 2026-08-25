#pragma once

#include <memory>
#include <string>

#include "execute_recovery_sequence_dto.hpp"
#include "edge_control/anomaly_failsafe/domain/interlock_management/interlock_manager.hpp"
#include "edge_control/contracts/ports/outbound/i_failsafe_publisher.hpp"
#include "edge_control/contracts/ports/outbound/i_recovery_sequence.hpp"
#include "shared/logger/global_system_logger.hpp"

namespace sftwin::edge_control::anomaly_failsafe::application {

class ExecuteRecoverySequenceUseCase {
   public:
    ExecuteRecoverySequenceUseCase(
        std::shared_ptr<domain::InterlockManager> interlock_mgr,
        std::shared_ptr<IFailsafePublisher> failsafe_pub,
        std::shared_ptr<IRecoverySequence> recovery,
        std::shared_ptr<shared::GlobalSystemLogger> system_logger = nullptr);

    [[nodiscard]] RecoveryExecutionResultDto execute(const ExecuteRecoverySequenceRequestDto& request_dto);

   private:
    std::shared_ptr<domain::InterlockManager> _interlock_mgr;
    std::shared_ptr<IFailsafePublisher> _failsafe_pub;
    std::shared_ptr<IRecoverySequence> _recovery;
    std::shared_ptr<shared::GlobalSystemLogger> _system_logger;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::application
