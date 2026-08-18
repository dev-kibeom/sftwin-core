from dataclasses import dataclass


@dataclass(frozen=True)
class RecoverySequence:
    """복구/우회 시퀀스 명세를 캡슐화한 순수 도메인 값 객체"""

    sequence_id: str
    sequence_script: str

    def __post_init__(self) -> None:
        if not self.sequence_id or not self.sequence_id.strip():
            raise ValueError("sequence_id cannot be empty.")
        if not self.sequence_script or not self.sequence_script.strip():
            raise ValueError("sequence_script cannot be empty.")
