from pydantic import BaseModel, Field


class TokenRefreshResponseDto(BaseModel):
    """Access Token 재발급 성공 응답 DTO (ITD v1.0)"""

    access_token: str = Field(..., description="신규 서명된 JWT Access Token")
    expires_in_seconds: int = Field(
        default=3600, description="Access Token 만료 시간 (초)"
    )
