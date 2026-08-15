from typing import Any, Protocol


class IKpiQueryRepository(Protocol):
    """
    KPI 도메인 전용 읽기(Query) 포트 (시계열 DB 및 시뮬레이션 결과 조회)
    """

    def fetch_simulation_telemetry_logs(self, sim_id: str) -> list[dict[str, Any]]:
        """시뮬레이션 시계열 계측 로그 조회"""
        ...
