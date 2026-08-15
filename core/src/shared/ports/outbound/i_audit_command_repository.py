from typing import Any, Protocol


class IAuditRepository(Protocol):
    """감사 로그 저장을 위한 도메인 추상화 인터페이스"""

    def save(self, audit_dto: dict[str, Any]) -> None: ...
