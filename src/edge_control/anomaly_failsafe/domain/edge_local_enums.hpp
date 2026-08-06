#pragma once

namespace sftwin::edge_control::anomaly_failsafe::domain {

/**
 * @brief 에지 제어 엔진의 런타임 상태 라이프사이클 (FCN-EDG-003)
 */
enum class EdgeEngineState {
    ACTIVE_MONITORING,  // 정상 관제 중
    INTERLOCK_ENGAGED,  // 물리 릴레이 차단됨 (E-Stop 발동 상태)
    RECOVERY_PENDING    // 우회 궤적 및 복구 스크립트 대기/실행 중
};

/**
 * @brief C++ 내부 연산용 로컬 액션 열거형 (Protobuf IDL과 분리)
 */
enum class FailsafeActionEnum { NONE = 0, ESTOP = 1, PAUSE = 2, BYPASS = 3, RESUME = 4 };

}  // namespace sftwin::edge_control::anomaly_failsafe::domain