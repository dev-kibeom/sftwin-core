from typing import Protocol

from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)


class IBaselineCommandRepository(Protocol):
    """트윈 베이스라인 영속화 전담 아웃바운드 포트"""

    def find_by_id(self, baseline_id: str) -> TwinBaseline | None:
        """수정 작업을 위해 도메인 엔티티 형태로 DB에서 복원한다."""
        ...

    def save(self, baseline: TwinBaseline) -> None:
        """엔티티 저장 및 수정 (성공 시 None, 실패 시 예외)"""
        ...

    def delete_by_id(self, baseline_id: str) -> None:
        """식별자 기반 삭제 (물리 삭제 또는 is_deleted=True 논리 삭제)"""
        ...
