from enum import Enum


class AdapterCallState(str, Enum):
    """ROS 2 어댑터 RPC 호출 상태 열거형"""

    IDLE = "IDLE"
    REQUEST_IN_FLIGHT = "REQUEST_IN_FLIGHT"
    COMPLETED = "COMPLETED"
    TIMEOUT_EXCEEDED = "TIMEOUT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
