"""
Global Error Codes Specification

설계 의도:
GTS 4.1절 전역 에러 코드 구조(ERR_{DOMAIN}_{REASON})를 상수로 정의하여
시스템 전반에서 통용되는 에러 코드를 일관되게 유지합니다.
"""


class GlobalErrorCodes:
    """GTS 규격 공통 및 도메인 전역 에러 코드 상수"""

    # Common Global Errors
    ERR_COMMON_INVALID_INPUT = "ERR_COMMON_INVALID_INPUT"
    ERR_COMMON_UNAUTHORIZED = "ERR_COMMON_UNAUTHORIZED"
    ERR_COMMON_FORBIDDEN = "ERR_COMMON_FORBIDDEN"
    ERR_COMMON_INTERNAL_ERROR = "ERR_COMMON_INTERNAL_ERROR"

    # Twin & Asset Domain Errors
    ERR_TWIN_NOT_FOUND = "ERR_TWIN_NOT_FOUND"
    ERR_TWIN_SYNC_OVER_LIMIT = "ERR_TWIN_SYNC_OVER_LIMIT"

    # Simulation Domain Errors
    ERR_SIM_COLLISION_DETECTED = "ERR_SIM_COLLISION_DETECTED"

    # Edge Domain Errors
    ERR_EDGE_COMM_TIMEOUT = "ERR_EDGE_COMM_TIMEOUT"
    ERR_EDGE_FAILSAFE_TRIGGERED = "ERR_EDGE_FAILSAFE_TRIGGERED"
