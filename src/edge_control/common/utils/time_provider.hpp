#pragma once
#include <chrono>
#include <cstdint>

namespace sftwin::edge_control::common::utils {

/**
 * @brief 시스템 전역 시간 측정 유틸리티 (단일 책임)
 * 실시간 제어 루프의 일관성을 위해 steady_clock으로 통일합니다.
 */
class TimeProvider {
   public:
    // 나노초 단위의 단조 증가 시간 반환 (100ms 지연 측정 등 실시간성 계산용)
    static uint64_t get_steady_time_ns() {
        auto now = std::chrono::steady_clock::now().time_since_epoch();
        return std::chrono::duration_cast<std::chrono::nanoseconds>(now).count();
    }
};

}  // namespace sftwin::edge_control::common::utils