#pragma once
#include <string>

namespace sftwin::edge_control::anomaly_failsafe::ports {

/**
 * @brief Behavior Tree 복구 스크립트 실행을 위한 추상화 포트 (DIP)
 */
class IBehaviorTreeEngine {
   public:
    virtual ~IBehaviorTreeEngine() = default;
    virtual bool execute_script(const std::string& script) = 0;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::ports