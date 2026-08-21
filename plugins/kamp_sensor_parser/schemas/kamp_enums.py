from enum import Enum


class KampCncAxis(str, Enum):
    """KAMP 공작기계 대상 물리 축 식별자"""

    X = "X"
    Y = "Y"
    Z = "Z"
    SPINDLE = "S"


class KampSensorType(str, Enum):
    """KAMP 시계열 계측 센서 및 피드백 신호 타입"""

    ACTUAL_POSITION = "ACTUAL_POSITION"
    CURRENT_FEEDBACK = "CURRENT_FEEDBACK"
    OUTPUT_POWER = "OUTPUT_POWER"
    FEEDRATE = "FEEDRATE"
