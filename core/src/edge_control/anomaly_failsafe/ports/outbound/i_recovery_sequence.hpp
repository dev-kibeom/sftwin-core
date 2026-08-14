#pragma once
#include <string>

namespace sftwin::edge_control::anomaly_failsafe {

/**
 * @brief 이상 감지 후 복구/우회 시퀀스 제어를 담당하는 아웃바운드 포트
 * (BehaviorTree, Python Script, State Machine 등 세부 엔진 구현체로부터 독립)
 */
class IRecoverySequence {
   public:
    virtual ~IRecoverySequence() = default;

    // 도메인 친화적 메서드명
    virtual bool execute_recovery_sequence(const std::string& sequence_script) = 0;
};

}  // namespace sftwin::edge_control::anomaly_failsafe
