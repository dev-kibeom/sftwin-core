/**
 * @brief 파이썬 서빙용 Pybind11 래퍼 (Mockup for compilation)
 * C++의 연산 계층과 Python 비즈니스 계층을 연결합니다.
 */
#include <memory>
#include <string>

#include "edge_command_facade.hpp"

// 실제 빌드 시에는 #include <pybind11/pybind11.h>가 포함됩니다.

namespace sftwin::edge_control::facades {

class EdgeFacadePybind {
   private:
    std::shared_ptr<EdgeCommandFacadeCPP> _native_cpp_facade;

   public:
    explicit EdgeFacadePybind(std::shared_ptr<EdgeCommandFacadeCPP> native_facade)
        : _native_cpp_facade(std::move(native_facade)) {}

    void execute_failsafe_estop(const std::string& reason) {
        // Python 레이어에서 RBAC 토큰 검증 완료 후 호출됨.
        _native_cpp_facade->execute_failsafe_estop_native(reason.c_str());
    }

    bool resume_process(const std::string& command_script) {
        return _native_cpp_facade->resume_process_native(command_script);
    }
};

}  // namespace sftwin::edge_control::facades

// PYBIND11_MODULE(edge_facade, m) { ... }