from enum import Enum


class TwinSyncStatusEnum(str, Enum):
    """
    디지털 트윈 베이스라인 및 동기화 상태 열거형 (Global Enum)
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    TOLERANCE_EXCEEDED = "TOLERANCE_EXCEEDED"
    FAILED = "FAILED"
