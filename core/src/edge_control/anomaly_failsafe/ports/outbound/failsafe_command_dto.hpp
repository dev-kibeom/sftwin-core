#pragma once
#include <cstdint>
#include <string>

namespace sftwin::edge_control::anomaly_failsafe {

/**
 * @brief 순수 C++ 기반 Failsafe 명령 전송 DTO (Protobuf 의존성 100% 제거)
 */
class FailsafeCommandDto {
   private:
    std::string _target_device_id;
    std::string _action_type;
    std::string _trigger_reason;
    uint64_t _issued_timestamp_ns{0};

   public:
    FailsafeCommandDto() = default;

    FailsafeCommandDto(std::string target, std::string action, std::string reason, uint64_t timestamp_ns = 0)
        : _target_device_id(std::move(target)),
          _action_type(std::move(action)),
          _trigger_reason(std::move(reason)),
          _issued_timestamp_ns(timestamp_ns) {}

    [[nodiscard]] const std::string& target_device_id() const { return _target_device_id; }
    [[nodiscard]] const std::string& action_type() const { return _action_type; }
    [[nodiscard]] const std::string& trigger_reason() const { return _trigger_reason; }
    [[nodiscard]] uint64_t issued_timestamp_ns() const { return _issued_timestamp_ns; }
};

}  // namespace sftwin::edge_control::anomaly_failsafe
