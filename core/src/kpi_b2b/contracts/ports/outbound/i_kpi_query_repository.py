# File: sftwin_project/core/src/kpi_b2b/contracts/ports/outbound/i_kpi_query_repository.py

from typing import Protocol

from kpi_b2b.contracts.dtos.kpi_report_dto import KpiReportDto


class IKpiQueryRepository(Protocol):
    """KPI 리포트 및 메트릭 데이터 조회 전용 아웃바운드 포트"""

    def get_kpi_by_id(
        self,
        report_id: str,
        company_id: str,
    ) -> KpiReportDto | None:
        """단건 KPI 보고서 조회 (테넌트 격리)"""
        ...
