from pydantic import BaseModel, Field


class TokenRefreshRequestDto(BaseModel):
    """Access Token 재발급 요청 DTO (ITD v1.0)"""

    refresh_token: str = Field(..., description="유효한 JWT Refresh Token")
