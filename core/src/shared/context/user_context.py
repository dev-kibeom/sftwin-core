from dataclasses import dataclass, field

from shared.enums.user_role_enum import UserRoleEnum


@dataclass(frozen=True)
class UserContext:
    """인증된 사용자 컨텍스트"""

    user_id: str
    username: str
    company_id: str
    role: UserRoleEnum
    accessible_factory_ids: list[str] = field(default_factory=list)
    is_edge_authenticated: bool = False

    @classmethod
    def create_system_context(cls, company_id: str = "SYSTEM_PUBLIC") -> "UserContext":
        """시스템 내부 실행용 불변 UserContext 생성 팩토리 메서드"""

        return UserContext(
            user_id="SYSTEM",
            username="system",
            company_id=company_id,
            role=UserRoleEnum.SYSTEM_ADMIN,
            accessible_factory_ids=[],
            is_edge_authenticated=True,
        )
