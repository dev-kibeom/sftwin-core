from typing import Protocol

from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)


class IBaselineCommandRepository(Protocol):
    """트윈 베이스라인 영속화 전담 Command Port"""

    def load_by_id(self, baseline_id: str) -> TwinBaseline | None:
        """수정 작업을 위해 DB에서 베이스라인 엔티티를 복원합니다."""
        ...

    def save(self, baseline: TwinBaseline) -> None:
        """베이스라인 엔티티를 저장 및 갱신합니다."""
        ...

    def delete_by_id(self, baseline_id: str) -> bool:
        """식별자 기반 물리 삭제를 수행합니다."""
        ...
