from enum import Enum
from typing import Any


class GlobalErrorCode(str, Enum):
    # Common / Shared Infrastructure
    ERR_COMMON_INVALID_INPUT = "ERR_COMMON_INVALID_INPUT"
    ERR_COMMON_UNAUTHORIZED = "ERR_COMMON_UNAUTHORIZED"
    ERR_COMMON_FORBIDDEN = "ERR_COMMON_FORBIDDEN"
    ERR_COMMON_INTERNAL_ERROR = "ERR_COMMON_INTERNAL_ERROR"

    # Asset Twin Domain
    ERR_TWIN_NOT_FOUND = "ERR_TWIN_NOT_FOUND"
    ERR_TWIN_INVALID_SCHEMA = "ERR_TWIN_INVALID_SCHEMA"
    ERR_TWIN_SYNC_OVER_LIMIT = "ERR_TWIN_SYNC_OVER_LIMIT"
    ERR_TWIN_KAMP_PARSE_FAIL = "ERR_TWIN_KAMP_PARSE_FAIL"

    # Simulation Domain
    ERR_SIM_INVALID_SCENARIO = "ERR_SIM_INVALID_SCENARIO"
    ERR_SIM_COLLISION_DETECTED = "ERR_SIM_COLLISION_DETECTED"
    ERR_SIM_IPC_TIMEOUT = "ERR_SIM_IPC_TIMEOUT"
    ERR_SIM_BT_EVAL_FAILED = "ERR_SIM_BT_EVAL_FAILED"
    ERR_SIM_RESOURCE_EXHAUSTED = "ERR_SIM_RESOURCE_EXHAUSTED"

    # Edge Control Domain
    ERR_EDGE_COMM_TIMEOUT = "ERR_EDGE_COMM_TIMEOUT"
    ERR_EDGE_FAILSAFE_TRIGGERED = "ERR_EDGE_FAILSAFE_TRIGGERED"

    # B2B & KPI Domain
    ERR_B2B_API_FAILURE = "ERR_B2B_API_FAILURE"
    ERR_B2B_INVALID_QUOTE = "ERR_B2B_INVALID_QUOTE"
    ERR_KPI_DB_TIMEOUT = "ERR_KPI_DB_TIMEOUT"
    ERR_KPI_SIM_NOT_FOUND = "ERR_KPI_SIM_NOT_FOUND"

    # Shared Memory
    ERR_IPC_SHARED_MEMORY_ERROR = "ERR_IPC_SHARED_MEMORY_ERROR"


ERROR_CODE_METADATA: dict[GlobalErrorCode, dict[str, Any]] = {
    # 1. Common / Shared Infrastructure
    GlobalErrorCode.ERR_COMMON_INVALID_INPUT: {
        "status": 400,
        "msg": "요청 DTO 유효성 검증 실패 또는 필수 입력 필드 누락",
    },
    GlobalErrorCode.ERR_COMMON_UNAUTHORIZED: {
        "status": 401,
        "msg": "JWT 토큰 누락, 만료 또는 서명 검증 실패",
    },
    GlobalErrorCode.ERR_COMMON_FORBIDDEN: {
        "status": 403,
        "msg": "RBAC 역할 레벨 부족 또는 타 기업 데이터 접근 시도 (보안 감사)",
    },
    GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR: {
        "status": 500,
        "msg": "An unexpected internal server error occurred.",
    },
    GlobalErrorCode.ERR_IPC_SHARED_MEMORY_ERROR: {
        "status": 500,
        "msg": "POSIX Shared Memory 또는 IPC 서브시스템 연산 실패",
    },
    # 2. Asset Twin Domain
    GlobalErrorCode.ERR_TWIN_NOT_FOUND: {
        "status": 404,
        "msg": "요청한 AAS 자산 또는 3D 레이아웃이 존재하지 않음",
    },
    GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA: {
        "status": 400,
        "msg": "AAS 또는 기구학 메타데이터 스키마 규약 위반",
    },
    GlobalErrorCode.ERR_TWIN_SYNC_OVER_LIMIT: {
        "status": 422,
        "msg": "가상-현실 정합성 오차율 허용치(5.0%) 초과",
    },
    GlobalErrorCode.ERR_TWIN_KAMP_PARSE_FAIL: {
        "status": 500,
        "msg": "KAMP 센서 로그 파싱 및 연산 오류",
    },
    # 3. Simulation Domain
    GlobalErrorCode.ERR_SIM_INVALID_SCENARIO: {
        "status": 400,
        "msg": "시뮬레이션 시나리오 유효성 검증 실패 또는 베이스라인 미지정",
    },
    GlobalErrorCode.ERR_SIM_COLLISION_DETECTED: {
        "status": 409,
        "msg": "MuJoCo 연산 중 로봇 간 물리 충돌 또는 교착 상태 감지",
    },
    GlobalErrorCode.ERR_SIM_IPC_TIMEOUT: {
        "status": 500,
        "msg": "C++ 물리/RL 엔진 간 POSIX SHM 동기화 타임아웃 (> 1ms)",
    },
    GlobalErrorCode.ERR_SIM_BT_EVAL_FAILED: {
        "status": 422,
        "msg": "Behavior Tree XML 구조 오류 또는 우회 경로 탐색 불가",
    },
    GlobalErrorCode.ERR_SIM_RESOURCE_EXHAUSTED: {
        "status": 503,
        "msg": "GPU VRAM 메모리 임계치(4.2GB) 초과",
    },
    # 4. Edge Control Domain
    GlobalErrorCode.ERR_EDGE_COMM_TIMEOUT: {
        "status": 504,
        "msg": "로컬 OT/FastDDS 통신 패킷 수신 타임아웃 (> 100ms)",
    },
    GlobalErrorCode.ERR_EDGE_FAILSAFE_TRIGGERED: {
        "status": 503,
        "msg": "안전 임계치 초과로 100ms 이내 Failsafe E-Stop 발동",
    },
    # 5. B2B & KPI Domain
    GlobalErrorCode.ERR_B2B_API_FAILURE: {
        "status": 502,
        "msg": "외부 B2B 마켓플레이스 연동 실패 또는 타임아웃",
    },
    GlobalErrorCode.ERR_B2B_INVALID_QUOTE: {
        "status": 422,
        "msg": "외부 마켓플레이스 응답 견적 스키마 불일치",
    },
    GlobalErrorCode.ERR_KPI_DB_TIMEOUT: {
        "status": 500,
        "msg": "InfluxDB 시계열 쿼리 지연 또는 단절",
    },
    GlobalErrorCode.ERR_KPI_SIM_NOT_FOUND: {
        "status": 404,
        "msg": "대상 시뮬레이션 결과 데이터 미존재",
    },
}
