from pydantic import BaseModel, Field


class LoginRequestDto(BaseModel):
    """플랫폼 사용자 로그인 요청 DTO (ITD v1.0)"""

    username: str = Field(..., description="사용자 계정명")
    password: str = Field(..., description="사용자 비밀번호")
