from typing import Protocol

from kpi_b2b.kpi_dashboard.application.calculate_kpi.kpi_report_dto import KpiReportDto
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.dual_kpi_report_dto import (
    DualKpiReportDto,
)
from shared.context.user_context import UserContext


class IKpiQueryFacade(Protocol):
    def calculate_oee(self, sim_id: str, ctx: UserContext) -> KpiReportDto: ...

    def generate_dual_kpi_report(
        self,
        baseline_oee: float,
        improved_oee: float,
        baseline_fpy: float,
        improved_fpy: float,
        turnkey_quote_cost: float,
        ctx: UserContext,
    ) -> DualKpiReportDto: ...
