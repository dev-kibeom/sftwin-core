from typing import Protocol


class IKpiQueryRepository(Protocol):
    """
    KPI 도메인 전용 읽기(Query) 포트
    """

    def get_kpi(self) -> None: ...
