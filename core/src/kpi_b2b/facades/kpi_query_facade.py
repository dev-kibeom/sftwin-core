from typing import Any

from kpi_b2b.kpi_dashboard.application.calculate_kpi.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_dto import (
    GenerateDualKpiReportRequestDto,
)
from kpi_b2b.kpi_dashboard.application.generate_dual_kpi_report.generate_dual_kpi_report_usecase import (
    GenerateDualKpiReportUseCase,
)
from kpi_b2b.ports.inbound.dtos.dual_kpi_report_dto import DualKpiReportDto
from kpi_b2b.ports.inbound.dtos.kpi_report_dto import KpiReportDto
from kpi_b2b.ports.inbound.i_kpi_query_facade import IKpiQueryFacade
from shared.context.user_context import UserContext
from shared.security.rbac_authorization_manager import RbacAuthorizationManager


class KpiQueryFacade(IKpiQueryFacade):
    def __init__(
        self,
        calculate_kpi_uc: CalculateKpiUseCase,
        dual_kpi_uc: GenerateDualKpiReportUseCase,
        rbac_manager: RbacAuthorizationManager,
        sim_repo: Any = None,
    ):
        self._calculate_kpi_uc = calculate_kpi_uc
        self._dual_kpi_uc = dual_kpi_uc
        self._rbac_manager = rbac_manager
        self._sim_repo = sim_repo

    def calculate_oee(self, sim_id: str, ctx: UserContext) -> KpiReportDto:
        target_company_id = (
            self._sim_repo.get_owner(sim_id)
            if hasattr(self._sim_repo, "get_owner")
            else ctx.company_id
        )

        self._rbac_manager.validate_company_isolation(
            user_ctx=ctx,
            target_company_id=target_company_id,
            target_resource=f"SIMULATION:{sim_id}",
        )

        return self._calculate_kpi_uc.execute(sim_id=sim_id, ctx=ctx)

    def generate_dual_kpi_report(
        self, request_dto: GenerateDualKpiReportRequestDto, ctx: UserContext
    ) -> DualKpiReportDto:
        return self._dual_kpi_uc.execute(request_dto=request_dto, ctx=ctx)
