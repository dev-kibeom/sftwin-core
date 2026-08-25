#pragma once

#include <string>
#include <utility>

namespace sftwin::edge_control {

class RecoveryExecutionResultDto {
   public:
    RecoveryExecutionResultDto() = default;

    RecoveryExecutionResultDto(bool success, std::string message = "", std::string error_code = "")
        : _is_success(success),
          _error_message(std::move(message)),
          _error_code(std::move(error_code)) {}

    [[nodiscard]] bool is_success() const noexcept { return _is_success; }
    [[nodiscard]] const std::string& error_message() const noexcept { return _error_message; }
    [[nodiscard]] const std::string& error_code() const noexcept { return _error_code; }

    static RecoveryExecutionResultDto success() {
        return RecoveryExecutionResultDto(true);
    }

    static RecoveryExecutionResultDto failure(std::string message, std::string error_code = "ERR_SIM_RECOVER_EVAL_FAILED") {
        return RecoveryExecutionResultDto(false, std::move(message), std::move(error_code));
    }

   private:
    bool _is_success{false};
    std::string _error_message;
    std::string _error_code;
};

}  // namespace sftwin::edge_control
