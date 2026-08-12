"""
@file session_data_dto.py
@description 3D 미러링 데이터 스트리밍 접근을 위한 1회성 세션 토큰 응답 DTO
"""

from dataclasses import dataclass


@dataclass
class SessionDataDto:
    session_id: str
    session_token: str
    status: str
    expires_in_seconds: int
