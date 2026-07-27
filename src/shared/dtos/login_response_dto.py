from pydantic import BaseModel, Field


class LoginResponseDto(BaseModel):
    """플랫폼 사용자 로그인 성공 응답 DTO (ITD v1.0)"""

    access_token: str = Field(..., description="서명된 JWT Access Token")
    refresh_token: str = Field(..., description="서명된 JWT Refresh Token")
    token_type: str = Field(default="Bearer", description="토큰 인증 타입")
    expires_in_seconds: int = Field(
        default=3600, description="Access Token 만료 시간 (초)"
    )
