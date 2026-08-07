"""
@file packml_state_enum.py
@description ISA-88/PackML 및 VDA 5050 표준 규격에 따른 현장 설비 실시간 상태 열거형
"""

from enum import Enum


class PackMLStateEnum(str, Enum):
    OFFLINE = "OFFLINE"
    STOPPED = "STOPPED"
    IDLE = "IDLE"
    STARTING = "STARTING"
    EXECUTE = "EXECUTE"
    HOLDING = "HOLDING"
    HELD = "HELD"
    UNHOLDING = "UNHOLDING"
    SUSPENDED = "SUSPENDED"
    COMPLETING = "COMPLETING"
    COMPLETE = "COMPLETE"
    ABORTING = "ABORTING"
    ABORTED = "ABORTED"
