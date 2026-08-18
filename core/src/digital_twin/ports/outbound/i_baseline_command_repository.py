# i_baseline_command_repository.py
from typing import Protocol

from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)


class IBaselineCommandRepository(Protocol):
    """트윈 베이스라인 영속화 전담 아웃바운드 포트"""

    def save(self, baseline: TwinBaseline) -> TwinBaseline: ...

    def delete(self, baseline_id: str) -> bool: ...
