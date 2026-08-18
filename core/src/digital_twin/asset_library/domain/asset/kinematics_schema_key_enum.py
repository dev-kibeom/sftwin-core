from enum import Enum


class KinematicsSchemaKey(str, Enum):
    """자산 기구학 메타데이터 스키마 필수 키 정의"""

    DEGREES_OF_FREEDOM = "degrees_of_freedom"
    DH_PARAMETERS = "dh_parameters"
