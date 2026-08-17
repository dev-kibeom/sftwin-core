from typing import Any, Protocol


class IAuditCommandRepository(Protocol):
    """감사 이력 영속화를 위한 전사 표준 Outbound Port"""

    def save(self, audit_dto: dict[str, Any]) -> None: ...
