#pragma once

#include <cstdint>
#include <string>
#include <utility>

namespace sftwin::edge_control {

class FailsafeCommandDto {
   public:
    FailsafeCommandDto() = default;

    FailsafeCommandDto(std::string target, std::string action, std::string reason,
                       uint64_t timestamp_ns = 0)
        : _target_device_id(std::move(target)),
          _action_type(std::move(action)),
          _trigger_reason(std::move(reason)),
          _issued_timestamp_ns(timestamp_ns) {}

    [[nodiscard]] const std::string& target_device_id() const noexcept { return _target_device_id; }
    [[nodiscard]] const std::string& action_type() const noexcept { return _action_type; }
    [[nodiscard]] const std::string& trigger_reason() const noexcept { return _trigger_reason; }
    [[nodiscard]] uint64_t issued_timestamp_ns() const noexcept { return _issued_timestamp_ns; }

   private:
    std::string _target_device_id;
    std::string _action_type;
    std::string _trigger_reason;
    uint64_t _issued_timestamp_ns{0};
};

}  // namespace sftwin::edge_control
