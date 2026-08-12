"""
@file base_time_series_port.py
@description 시계열 DB 조회를 위한 추상 포트 (DIP 준수)
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTimeSeriesPort(ABC):
    @abstractmethod
    def fetch_simulation_logs(self, sim_id: str) -> list[dict[str, Any]]:
        """
        주어진 시뮬레이션 ID에 해당하는 시계열 로그 배열을 반환합니다.
        """
        pass
