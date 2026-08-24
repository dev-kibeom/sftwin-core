from typing import Protocol

from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_dto import (
    GenerateDualKpiReportRequestDto,
)
from kpi_b2b.contracts.dtos.dual_kpi_report_dto import DualKpiReportDto
from kpi_b2b.contracts.dtos.kpi_report_dto import KpiReportDto
from shared.context.user_context import UserContext


class IKpiQueryFacade(Protocol):
    def calculate_oee(self, sim_id: str, ctx: UserContext) -> KpiReportDto: ...

    def generate_dual_kpi_report(
        self, request_dto: GenerateDualKpiReportRequestDto, ctx: UserContext
    ) -> DualKpiReportDto: ...
