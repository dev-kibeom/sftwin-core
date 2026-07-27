from enum import Enum

from pydantic import BaseModel, Field


class UserRoleEnum(str, Enum):
    """RBAC 역할 명세 (GTS v2.0 / ITD v1.0)"""

    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    FACTORY_MANAGER = "FACTORY_MANAGER"
    FIELD_ENGINEER = "FIELD_ENGINEER"
    SI_PARTNER = "SI_PARTNER"
    CREATOR = "CREATOR"


class UserContext(BaseModel):
    """인증 컨텍스트 DTO"""

    user_id: str = Field(..., description="인증된 사용자 고유 ID (UUID)")
    username: str = Field(..., description="사용자 계정명")
    company_id: str = Field(..., description="속한 제조기업/SI업체 식별자")
    role: UserRoleEnum = Field(..., description="부여된 RBAC 권한 역할")
    accessible_factory_ids: list[str] = Field(
        default_factory=list, description="접근 허용된 공장 ID 목록"
    )
    is_edge_authenticated: bool = Field(
        default=False, description="에지 로컬 관제용 인증 여부"
    )
