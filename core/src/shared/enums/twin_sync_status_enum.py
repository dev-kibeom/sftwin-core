"""
===============================================================================
[File Name] twin_sync_status_enum.py
[Location ] /src/shared/enums/twin_sync_status_enum.py
[Description]
 - 디지털 트윈 베이스라인 및 가상-현실 동기화 상태를 정의하는 전역 열거형 상수입니다.
 - GTS v3.0 및 전역 도메인 공통 규격을 준수합니다.
===============================================================================
"""

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
