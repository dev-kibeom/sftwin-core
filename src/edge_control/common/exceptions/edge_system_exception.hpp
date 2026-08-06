#pragma once
#include <stdexcept>
#include <string>

namespace sftwin::edge_control::common::exceptions {

/**
 * @brief 에지 관제 시스템 전용 커스텀 예외 클래스
 * GTS 전역 에러 코드 매트릭스의 'ERR_EDGE_*' 규격을 준수합니다.
 */
class EdgeSystemException : public std::runtime_error {
   private:
    std::string _error_code;

   public:
    EdgeSystemException(const std::string& error_code, const std::string& message)
        : std::runtime_error(message), _error_code(error_code) {}

    [[nodiscard]] std::string get_error_code() const { return _error_code; }
};

}  // namespace sftwin::edge_control::common::exceptions