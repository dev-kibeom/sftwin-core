#pragma once

#include <stdexcept>
#include "interlock_state_enum.hpp"

namespace sftwin::edge_control::anomaly_failsafe::domain {

class InterlockManager {
   public:
    explicit InterlockManager(InterlockState initial_state = InterlockState::RELEASED)
        : _state(initial_state) {}

    [[nodiscard]] InterlockState state() const noexcept { return _state; }

    void engage_estop() noexcept {
        _state = InterlockState::ENGAGED;
    }

    void start_recovery() {
        if (_state != InterlockState::ENGAGED) {
            throw std::logic_error("Cannot start recovery unless interlock is ENGAGED.");
        }
        _state = InterlockState::PENDING_RESET_APPROVAL;
    }

    void cancel_recovery() noexcept {
        _state = InterlockState::ENGAGED;
    }

    void release() {
        if (_state == InterlockState::RELEASED) {
            return;
        }
        _state = InterlockState::RELEASED;
    }

   private:
    InterlockState _state;
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
