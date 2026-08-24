from typing import Protocol

from kpi_b2b.contracts.dtos.telemetry_summary_dto import TelemetrySummaryDto


class ITelemetryQueryRepository(Protocol):
    """시뮬레이션 및 센서 시계열 계측 요약 데이터 조회 전용 아웃바운드 포트"""

    def get_telemetry_summary_by_sim_id(
        self, sim_id: str, company_id: str
    ) -> TelemetrySummaryDto | None:
        """테넌시 격리가 적용된 시뮬레이션 계측 통계 요약 조회 (IDOR 방어)"""
        ...
