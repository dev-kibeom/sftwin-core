"""
===============================================================================
[File Name] asset_type_enum.py
[Location ] /src/shared/enums/asset_type_enum.py
[Description]
 - AAS 자산 라이브러리 및 3D 가상 공간 내 자산 종류를 정의하는 전역 열거형 상수입니다.
 - GTS v3.0 명세 규격을 엄격히 준수합니다.
===============================================================================
"""

from enum import Enum


class AssetTypeEnum(str, Enum):
    """
    AAS 자산 분류 코드 열거형 (GTS v3.0)
    """

    ROBOT = "ROBOT"
    AMR = "AMR"
    HUMANOID = "HUMANOID"
    CNC = "CNC"
    INJECTION_MOLDING = "INJECTION_MOLDING"
    CONVEYOR = "CONVEYOR"
    SENSOR = "SENSOR"
