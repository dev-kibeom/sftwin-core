#pragma once

#include <stdexcept>
#include <string>
#include <utility>

namespace sftwin::shared {

class GlobalExceptionHandler : public std::runtime_error {
   public:
    GlobalExceptionHandler(std::string error_code, const std::string& message)
        : std::runtime_error(message), _error_code(std::move(error_code)) {}

    [[nodiscard]] const std::string& get_error_code() const noexcept { return _error_code; }

   private:
    std::string _error_code;
};

}  // namespace sftwin::shared
