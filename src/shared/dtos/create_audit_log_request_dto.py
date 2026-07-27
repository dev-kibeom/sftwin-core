from typing import Any

from pydantic import BaseModel, Field


class CreateAuditLogRequestDto(BaseModel):
    """감사 로그 영속화 요청 DTO"""

    trace_id: str = Field(..., description="분산 트레이싱 ID")
    component_name: str = Field(..., description="발행 컴포넌트 명칭")
    action_type: str = Field(
        ..., description="감사 행위 분류 (예: FAILSAFE_ESTOP, LOGIN)"
    )
    severity: str = Field(..., description="심각도 (INFO, WARN, CRITICAL)")
    target_resource: str = Field(..., description="대상 리소스/디바이스 ID")
    details: dict[str, Any] | None = Field(
        default_factory=dict, description="상세 콘텍스트 내역"
    )
