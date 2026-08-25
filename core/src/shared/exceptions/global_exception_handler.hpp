#pragma once

#include <stdexcept>
#include <string>
#include <string_view>
#include "global_error_code_enum.hpp"

namespace sftwin::shared {

class GlobalExceptionHandler : public std::runtime_error {
   public:
    // GlobalErrorCode enum만 허용 (string 생성자 제거)
    GlobalExceptionHandler(GlobalErrorCode error_code, const std::string& message)
        : std::runtime_error(message), _error_code(error_code) {}

    // enum 반환
    [[nodiscard]] GlobalErrorCode get_error_code() const noexcept {
        return _error_code;
    }

    // 문자열 형태의 에러 코드가 필요할 때 사용 ("ERR_COMMON_INVALID_INPUT" 등)
    [[nodiscard]] std::string_view get_error_code_str() const noexcept {
        return toString(_error_code);
    }

    // HTTP status 등이 필요할 때 바로 메타데이터 접근 가능
    [[nodiscard]] ErrorCodeMetadata get_metadata() const noexcept {
        return getMetadata(_error_code);
    }

   private:
    GlobalErrorCode _error_code;
};

}  // namespace sftwin::shared
