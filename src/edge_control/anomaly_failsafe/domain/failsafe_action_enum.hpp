#pragma once

namespace sftwin::edge_control::anomaly_failsafe::domain {

/**
 * @brief 하드웨어 및 시스템 레벨 비상 조치 판정 열거형
 */
enum class FailsafeActionEnum {
    NONE = 0,   // 정상 상태 (조치 불필요)
    ESTOP = 1,  // 즉각적인 물리 전원/동력 차단 (치명적 위반)
    PAUSE = 2,  // 공정 일시 정지
    BYPASS = 3  // 우회 궤적 가동 (주의 구역 진입 등)
};

}  // namespace sftwin::edge_control::anomaly_failsafe::domain