from pydantic import BaseModel, Field


class SystemConfigDto(BaseModel):
    """공통 시스템 설정 조회 응답 DTO (ITD v1.0)"""

    config_key: str = Field(..., description="시스템 설정 고유 키")
    config_value: str = Field(..., description="시스템 설정 값")
    description: str = Field(..., description="설명 및 타임아웃 정보")
    updated_at: str = Field(..., description="최종 수정 일시 (ISO-8601 UTC)")
