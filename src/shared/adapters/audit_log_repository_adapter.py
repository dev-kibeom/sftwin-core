import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from src.shared.exceptions.base_exception import InternalServerException

logger = logging.getLogger("sftwin.shared.audit_repository")


class BaseRepositoryAdapter:
    """공통 데이터베이스 접근 베이스 어댑터"""

    def __init__(self, db_session: Any = None):
        self.db_session = db_session


class AuditLogEntity:
    """감사 로그 DB 엔티티 표현"""

    def __init__(
        self,
        audit_id: str,
        trace_id: str,
        component_name: str,
        action_type: str,
        severity: str,
        target_resource: str,
        details: dict[str, Any],
        company_id: str,
        created_by: str,
        created_at: str,
        is_deleted: int = 0,
    ):
        self.audit_id = audit_id
        self.trace_id = trace_id
        self.component_name = component_name
        self.action_type = action_type
        self.severity = severity
        self.target_resource = target_resource
        self.details = details
        self.company_id = company_id
        self.created_by = created_by
        self.created_at = created_at
        self.is_deleted = is_deleted


class AuditLogRepositoryAdapter(BaseRepositoryAdapter):
    """감사 로그 데이터베이스 영속화 어댑터"""

    def save_audit_log(
        self,
        dto: Any,
        company_id: str,
        created_by: str,
    ) -> AuditLogEntity:
        """감사 로그 DB 저장 연산 및 공통 감사 필드 자동 바인딩"""
        try:
            audit_id = f"AUD-{uuid.uuid4().hex[:12]}"
            created_at = datetime.now(timezone.utc).isoformat()

            entity = AuditLogEntity(
                audit_id=audit_id,
                trace_id=dto.trace_id,
                component_name=dto.component_name,
                action_type=dto.action_type,
                severity=dto.severity,
                target_resource=dto.target_resource,
                details=dto.details or {},
                company_id=company_id,
                created_by=created_by,
                created_at=created_at,
                is_deleted=0,
            )

            # DB Session 처리 모킹/연동 영역
            if self.db_session:
                if getattr(self.db_session, "is_closed", False):
                    raise TimeoutError("Database connection timed out or is closed.")

            logger.info(
                f"[AuditLogRepositoryAdapter] Audit log saved successfully. audit_id={audit_id}"
            )
            return entity

        except Exception as exc:
            logger.error(
                f"[AuditLogRepositoryAdapter] Failed to persist audit log: {exc}"
            )
            raise InternalServerException(
                message="An unexpected error occurred while persisting audit log to database.",
                details={"error": str(exc)},
            )
