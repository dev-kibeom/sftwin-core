#pragma once
#include <string>

namespace sftwin::edge_control::ports::inbound {

class IEdgeCommandFacade {
   public:
    virtual ~IEdgeCommandFacade() = default;

    // 1. 비상 정지 발동
    virtual void execute_failsafe_estop(const char* reason) = 0;

    // 2.복구 시퀀스 실행
    virtual bool resume_process(const std::string& sequence_script) = 0;

    // 3. 2단계 현장 안전 점검 승인 기반 E-Stop 인터록 해제
    virtual bool reset_estop_2step(bool is_field_inspected, bool is_manager_approved) = 0;
};

}  // namespace sftwin::edge_control::ports::inbound
