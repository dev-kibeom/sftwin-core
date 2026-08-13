"""
===============================================================================
[File Name] i_twin_query_repository.py
[Location ] /src/asset_twin/twin_reconstruction/ports/outbound/i_twin_query_repository.py
[Description]
 - 3D 가상 공장 레이아웃 및 베이스라인 조회 전담(CQRS Read-Only) 포트 인터페이스입니다.
===============================================================================
"""

from abc import ABC, abstractmethod
from typing import Any


class ITwinQueryRepository(ABC):
    """
    읽기 전용 레이아웃 조회용 아웃바운드 포트 인터페이스 (CQRS Read)
    """

    @abstractmethod
    def find_baseline_with_mappings(self, baseline_id: str) -> dict[str, Any] | None:
        pass
