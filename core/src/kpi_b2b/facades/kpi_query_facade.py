# File: sftwin_project/core/src/kpi_b2b/facades/kpi_query_facade.py

from kpi_b2b.contracts.dtos.dual_kpi_report_dto import DualKpiReportDto
from kpi_b2b.contracts.dtos.kpi_report_dto import KpiReportDto
from kpi_b2b.contracts.ports.inbound.i_kpi_query_facade import IKpiQueryFacade
from kpi_b2b.kpi_dashboard.application.calculate_kpi.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_dto import (
    GenerateDualKpiReportRequestDto,
)
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_usecase import (
    GenerateDualKpiReportUseCase,
)
from shared.context.user_context import UserContext
from shared.security.context_guard import require_permission
from shared.security.user_role_enum import UserRole


class KpiQueryFacade(IKpiQueryFacade):
    def __init__(
        self,
        calculate_kpi_uc: CalculateKpiUseCase,
        dual_kpi_uc: GenerateDualKpiReportUseCase,
    ):
        self._calculate_kpi_uc = calculate_kpi_uc
        self._dual_kpi_uc = dual_kpi_uc

    @require_permission(UserRole.FIELD_ENGINEER, "KPI_CALCULATE_OEE")
    def get_oee(self, sim_id: str, ctx: UserContext) -> KpiReportDto:
        return self._calculate_kpi_uc.execute(sim_id=sim_id, ctx=ctx)

    @require_permission(UserRole.FIELD_ENGINEER, "KPI_DUAL_REPORT")
    def get_dual_kpi_report(
        self, request_dto: GenerateDualKpiReportRequestDto, ctx: UserContext
    ) -> DualKpiReportDto:
        return self._dual_kpi_uc.execute(request_dto=request_dto, ctx=ctx)
