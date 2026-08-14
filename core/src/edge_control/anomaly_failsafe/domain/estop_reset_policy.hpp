#pragma once
#include <string>

#include "edge_local_enums.hpp"
#include "src/edge_control/common/exceptions/edge_system_exception.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

/**
 * @brief E-Stop 발동 후 2단계 현장 안전 점검 승인 절차를 검증하는 도메인 정책 (ISO 13849-1 준수)
 */
class EstopResetPolicy {
   public:
    bool validate_reset_request(EdgeEngineState current_state, bool is_field_inspected,
                                bool is_manager_approved) const {
        if (current_state != domain::EdgeEngineState::INTERLOCK_ENGAGED) {
            throw EdgeSystemException(
                "ERR_COMMON_INVALID_INPUT",
                "Cannot reset E-Stop when engine state is not INTERLOCK_ENGAGED.");
        }

        if (!is_field_inspected || !is_manager_approved) {
            throw EdgeSystemException(
                "ERR_COMMON_FORBIDDEN",
                "E-Stop reset rejected. Both field inspection and manager approval are required.");
        }

        return true;
    }
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
