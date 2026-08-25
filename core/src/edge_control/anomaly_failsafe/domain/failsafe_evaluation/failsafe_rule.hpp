#pragma once

#include <cstdint>

namespace sftwin::edge_control::anomaly_failsafe::domain {

struct FailsafeRule {
    float max_torque_limit_nm = 150.5f;              // 물리 토크 최대 허용치 (Nm)
    uint64_t heartbeat_timeout_ns = 100'000'000ULL;  // 통신 지연 허용치 (100ms)
    float vision_critical_distance_m = 0.5f;         // 치명적 침입 반경 (0.5m)
    float vision_warning_distance_m = 1.5f;          // 주의 반경 (1.5m)
    float max_anomaly_score = 0.85f;                 // 시계열 이상 점수 최대치
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain
