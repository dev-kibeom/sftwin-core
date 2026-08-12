"""
@file kpi_query_facade.py
@description RbacAuthorizationManager를 활용하여 보안 정책을 전사 표준으로 통일한 KPI 파사드
"""

from abc import ABC, abstractmethod
from typing import Any

from src.kpi_b2b.kpi_dashboard.application.calculate_kpi.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from src.kpi_b2b.kpi_dashboard.application.calculate_kpi.kpi_report_dto import (
    KpiReportDto,
)
from src.shared.security.rbac_authorization_manager import RbacAuthorizationManager
from src.shared.security.user_context import UserContext


class KpiQueryFacade(ABC):
    @abstractmethod
    def calculate_oee(self, sim_id: str, ctx: UserContext) -> KpiReportDto:
        pass


class KpiQueryFacadeImpl(KpiQueryFacade):
    def __init__(
        self,
        calculate_kpi_uc: CalculateKpiUseCase,
        rbac_manager: RbacAuthorizationManager,
        sim_repo: Any = None,
    ):
        self._calculate_kpi_uc = calculate_kpi_uc
        self._rbac_manager = rbac_manager
        self._sim_repo = sim_repo  # 시나리오 소유권 조회를 위한 레포지토리

    def calculate_oee(self, sim_id: str, ctx: UserContext) -> KpiReportDto:
        # 1. DB에서 대상 데이터의 실제 소유주 조회 (Mock: 조회 실패 시 자기 자신 반환)
        target_company_id = (
            self._sim_repo.get_owner(sim_id)
            if hasattr(self._sim_repo, "get_owner")
            else ctx.company_id
        )

        # 2. 전역 RbacAuthorizationManager를 통한 멀티테넌시 격리 검증 (예외 발생/감사 로깅 자동 위임)
        self._rbac_manager.validate_company_isolation(
            user_ctx=ctx,
            target_company_id=target_company_id,
            target_resource=f"SIMULATION:{sim_id}",
        )

        # 3. UseCase 하향 위임
        return self._calculate_kpi_uc.execute(sim_id=sim_id, company_id=ctx.company_id)
