from dataclasses import dataclass

from .expert_session_status_enum import ExpertSessionStatus


@dataclass
class ExpertSession:
    """전문가 트윈 미러링 상담 세션 도메인 엔티티"""

    session_id: str
    baseline_id: str
    session_token: str
    expert_id: str = "UNASSIGNED"
    status: ExpertSessionStatus = ExpertSessionStatus.WAITING
    expires_in_seconds: int = 14400  # 기본 4시간 유효

    def __post_init__(self) -> None:
        if not self.session_id or not self.session_id.strip():
            raise ValueError("Valid session_id is required.")
        if not self.baseline_id or not self.baseline_id.strip():
            raise ValueError("Valid baseline_id is required.")
        if not self.session_token or not self.session_token.strip():
            raise ValueError("Valid session_token is required.")
        if self.expires_in_seconds <= 0:
            raise ValueError("expires_in_seconds must be greater than zero.")

    def assign_expert(self, expert_id: str) -> None:
        """세션에 전문가 배정 및 ACTIVE 전이"""
        if not expert_id or not expert_id.strip():
            raise ValueError("Valid expert_id is required.")
        if self.status != ExpertSessionStatus.WAITING:
            raise ValueError(
                f"Cannot assign expert to session in '{self.status.value}' state."
            )

        self.expert_id = expert_id
        self.status = ExpertSessionStatus.ACTIVE

    def close(self) -> None:
        """세션 정상 종료"""
        if self.status == ExpertSessionStatus.CLOSED:
            raise ValueError("Session is already closed.")
        self.status = ExpertSessionStatus.CLOSED
