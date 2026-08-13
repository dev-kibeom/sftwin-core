// core/src/edge_control/anomaly_failsafe/ports/i_hardware_interlock.hpp
#pragma once

namespace sftwin::edge_control::anomaly_failsafe::ports {

enum class InterlockState {
    RELEASED = 0,
    ENGAGED = 1,
    PENDING_RESET_APPROVAL = 2
};

class IHardwareInterlock {
   public:
    virtual ~IHardwareInterlock() = default;

    // 비상 정지 릴레이 차단
    virtual void trigger_physical_relay() = 0;

    // 안전 복구용 인터페이스
    virtual bool release_interlock(const std::string& operator_approval_token) = 0;
    virtual InterlockState get_state() const = 0;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::ports
