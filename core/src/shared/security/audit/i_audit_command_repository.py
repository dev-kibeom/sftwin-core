from typing import Protocol

from .audit_log_dto import AuditLogDto


class IAuditCommandRepository(Protocol):
    """감사 이력 영속화를 위한 전사 표준 Outbound Port"""

    def save(self, audit_dto: AuditLogDto) -> None: ...
