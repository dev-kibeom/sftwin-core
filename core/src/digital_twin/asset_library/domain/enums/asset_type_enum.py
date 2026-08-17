from enum import Enum


class AssetTypeEnum(str, Enum):
    """AAS 자산 분류 코드 열거형"""

    ROBOT = "ROBOT"
    AMR = "AMR"
    HUMANOID = "HUMANOID"
    CNC = "CNC"
    INJECTION_MOLDING = "INJECTION_MOLDING"
    CONVEYOR = "CONVEYOR"
    SENSOR = "SENSOR"
