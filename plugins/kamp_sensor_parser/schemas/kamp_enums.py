from enum import Enum


class KampCncAxis(str, Enum):
    """KAMP CNC 공정 가공 축 및 스핀들 식별자"""

    X = "X"
    Y = "Y"
    Z = "Z"
    SPINDLE = "S"


class KampSensorType(str, Enum):
    """KAMP 원시 계측 센서 항목 분류"""

    ACTUAL_POSITION = "ACTUAL_POSITION"
    CURRENT_FEEDBACK = "CURRENT_FEEDBACK"
    OUTPUT_POWER = "OUTPUT_POWER"
    FEEDRATE = "FEEDRATE"
    ACCELERATION = "ACCELERATION"


class KampJointAxis(str, Enum):
    """6축 로봇 및 CNC 가공 기구학 조인트 회전축 식별자 (FCN-KMP-004)"""

    JOINT_1 = "theta_1"
    JOINT_2 = "theta_2"
    JOINT_3 = "theta_3"
    JOINT_4 = "theta_4"
    JOINT_5 = "theta_5"
    JOINT_6 = "theta_6"
