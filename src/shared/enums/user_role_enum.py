from enum import Enum


class UserRoleEnum(str, Enum):
    """RBAC 사용자 및 접근 권한 역할 열거형 (GTS 3.1)"""

    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    FACTORY_MANAGER = "FACTORY_MANAGER"
    FIELD_ENGINEER = "FIELD_ENGINEER"
    SI_PARTNER = "SI_PARTNER"
    CREATOR = "CREATOR"
