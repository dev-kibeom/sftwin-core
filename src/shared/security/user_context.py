"""
UserContext Data Structure

설계 의도:
인증된 사용자의 식별자, 소속 기업 ID, 역할(UserRoleEnum), 접근 허용 공장 목록 등을 보유하는
Immutable(불변) 데이터 구조를 제공하여 인증 컨텍스트의 임의 오염을 방지합니다.
"""

from dataclasses import dataclass, field
from enum import Enum


class UserRoleEnum(str, Enum):
    """RBAC 사용자 및 접근 권한 역할 열거형 (GTS 3.1)"""

    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    FACTORY_MANAGER = "FACTORY_MANAGER"
    FIELD_ENGINEER = "FIELD_ENGINEER"
    SI_PARTNER = "SI_PARTNER"
    CREATOR = "CREATOR"


@dataclass(frozen=True)
class UserContext:
    """인증된 사용자 컨텍스트 (Immutable Data Holder)"""

    user_id: str
    username: str
    company_id: str
    role: UserRoleEnum
    accessible_factory_ids: list[str] = field(default_factory=list)
    is_edge_authenticated: bool = False
