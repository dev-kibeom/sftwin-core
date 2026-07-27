from pydantic import BaseModel, Field


class AuditLogResponseDto(BaseModel):
    """감사 로그 영속화 응답 DTO"""

    audit_id: str = Field(..., description="생성된 감사 로그 고유 식별자 (UUID v4)")
    created_at: str = Field(..., description="생성 시각 (ISO-8601 UTC)")
