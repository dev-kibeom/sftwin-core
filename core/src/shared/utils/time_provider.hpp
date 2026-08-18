#pragma once

#include <chrono>
#include <cstdint>

namespace sftwin::shared {

class GlobalTimeProvider {
   public:
    static uint64_t get_steady_time_ns() {
        const auto now = std::chrono::steady_clock::now().time_since_epoch();
        return std::chrono::duration_cast<std::chrono::nanoseconds>(now).count();
    }
};

}  // namespace sftwin::shared
