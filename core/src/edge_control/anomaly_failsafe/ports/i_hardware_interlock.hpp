#pragma once
namespace sftwin::edge_control::anomaly_failsafe::ports {
class IHardwareInterlock {
   public:
    virtual ~IHardwareInterlock() = default;
    virtual void trigger_physical_relay() = 0;
};
}  // namespace sftwin::edge_control::anomaly_failsafe::ports
