from fastapi import APIRouter

from src.shared.adapters.audit_log_repository_adapter import AuditLogRepositoryAdapter
from src.shared.dtos.audit_log_response_dto import AuditLogResponseDto
from src.shared.dtos.create_audit_log_request_dto import CreateAuditLogRequestDto
from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.logging.audit_logger import AuditLogger
from src.shared.security.user_context import UserContext

router = APIRouter(prefix="/api/v1/shared", tags=["Audit Log Management"])


class AuditLogController:
    """감사 로그 영속화 API 컨트롤러"""

    def __init__(
        self,
        repository: AuditLogRepositoryAdapter | None = None,
        audit_logger: AuditLogger | None = None,
    ):
        self.repository = repository or AuditLogRepositoryAdapter()
        self.audit_logger = audit_logger or AuditLogger()

    def create_audit_log(
        self,
        req: CreateAuditLogRequestDto,
        user_ctx: UserContext,
    ) -> GlobalResponseDto[AuditLogResponseDto]:
        """POST /api/v1/shared/audit-logs 구현"""
        company_id = user_ctx.company_id if user_ctx else "SYSTEM"
        created_by = user_ctx.user_id if user_ctx else "SYSTEM"

        # 1. DB Persistence
        saved_entity = self.repository.save_audit_log(
            dto=req,
            company_id=company_id,
            created_by=created_by,
        )

        # 2. Audit Logging Delegation
        self.audit_logger.log_security_event(
            user_ctx=user_ctx,
            action=req.action_type,
            target=req.target_resource,
            trace_id=req.trace_id,
            details=req.details,
        )

        # 3. Response DTO Build
        response_dto = AuditLogResponseDto(
            audit_id=saved_entity.audit_id,
            created_at=saved_entity.created_at,
        )

        return GlobalResponseDto.success_response(
            data=response_dto,
            message="Audit log created and persisted successfully.",
            trace_id=req.trace_id,
        )
