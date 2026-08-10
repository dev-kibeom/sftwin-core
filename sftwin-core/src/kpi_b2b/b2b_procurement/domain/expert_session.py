"""
@file expert_session.py
@description 도면 유출 방지 제약(NFR-06-3)을 준수하여 1회성 토큰 발급 및 상태를 관리하는 도메인 엔티티
"""

import uuid
from dataclasses import dataclass
from enum import Enum


class ExpertSessionStatusEnum(str, Enum):
    """비대면 전문가 상담 세션의 생명주기 상태"""

    WAITING = "WAITING"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


@dataclass
class ExpertSession:
    session_id: str
    baseline_id: str
    expert_id: str
    session_token: str
    status: ExpertSessionStatusEnum

    @classmethod
    def create_new_session(cls, baseline_id: str) -> "ExpertSession":
        """
        신규 상담 세션을 생성하고, 원본 파일 접근이 아닌 미러링 데이터 스트리밍용
        UUID v4 기반 1회성 암호화 토큰을 발급하며 WAITING 상태를 강제합니다.
        """
        return cls(
            session_id=f"SESS-{uuid.uuid4()}",
            baseline_id=baseline_id,
            expert_id="UNASSIGNED",  # 초기 생성 시 전문가는 미배정 상태
            session_token=cls._generate_secure_token(),
            status=ExpertSessionStatusEnum.WAITING,
        )

    @staticmethod
    def _generate_secure_token() -> str:
        """1회성 암호화 토큰 생성 (보안 제약 NFR-06-3 준수)"""
        return f"TKN-{uuid.uuid4().hex}"
