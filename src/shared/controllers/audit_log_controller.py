from fastapi import APIRouter, Depends, status

from src.shared.adapters.audit_log_repository_adapter import AuditLogRepositoryAdapter
from src.shared.dtos.audit_log_response_dto import AuditLogResponseDto
from src.shared.dtos.create_audit_log_request_dto import CreateAuditLogRequestDto
from src.shared.dtos.global_response_dto import GlobalResponseDto
from src.shared.logging.audit_logger import AuditLogger
from src.shared.security.user_context import UserContext

router = APIRouter(prefix="/api/v1/shared/audit-logs", tags=["Audit Log Management"])


class AuditLogService:
    """감사 로그 비즈니스 로직 및 영속화 위임 담당"""

    def __init__(
        self,
        repository: AuditLogRepositoryAdapter,
        audit_logger: AuditLogger,
    ):
        self.repository = repository
        self.audit_logger = audit_logger

    def create_and_notify_audit_log(
        self,
        req: CreateAuditLogRequestDto,
        user_ctx: UserContext | None,
    ) -> AuditLogResponseDto:
        # 1. 사용자 맥락 기본값 정제 (별도 도우미 메서드/프로퍼티로 추상화 가능)
        company_id = user_ctx.company_id if user_ctx else "SYSTEM"
        created_by = user_ctx.user_id if user_ctx else "SYSTEM"

        # 2. DB Persistence
        saved_entity = self.repository.save_audit_log(
            dto=req,
            company_id=company_id,
            created_by=created_by,
        )

        # 3. Audit Logging Delegation
        self.audit_logger.log_security_event(
            user_ctx=user_ctx,
            action=req.action_type,
            target=req.target_resource,
            trace_id=req.trace_id,
            details=req.details,
        )

        return AuditLogResponseDto(
            audit_id=saved_entity.audit_id,
            created_at=saved_entity.created_at,
        )


# FastAPI 라우터 엔드포인트 (추상화 수준 = 1)
@router.post("", status_code=status.HTTP_201_CREATED)
def create_audit_log(
    req: CreateAuditLogRequestDto,
    user_ctx: UserContext = Depends(get_current_user_context),  # 유저 컨텍스트 주입
    service: AuditLogService = Depends(),  # Service & Repository 의존성 자동 주입
) -> GlobalResponseDto[AuditLogResponseDto]:
    """POST /api/v1/shared/audit-logs"""

    # 서비스에 비즈니스 로직 위임 (성공 흐름만 깔끔하게 보임)
    response_dto = service.create_and_notify_audit_log(req, user_ctx)

    return GlobalResponseDto.success_response(
        data=response_dto,
        message="Audit log created and persisted successfully.",
        trace_id=req.trace_id,
    )
