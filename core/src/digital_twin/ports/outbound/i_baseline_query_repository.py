# i_baseline_query_repository.py
from typing import Protocol

from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)


class IBaselineQueryRepository(Protocol):
    """영속화된 트윈 베이스라인 조회 전담 아웃바운드 포트"""

    def find_by_id(self, baseline_id: str) -> TwinBaseline | None: ...
