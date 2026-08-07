"""
@file kpi_query_facade.py
@description 사용자 요청과 UseCase를 연결하고 권한/보안 인가를 처리하는 CQRS 쿼리 파사드
"""

from abc import ABC, abstractmethod

from src.kpi_b2b.kpi_dashboard.application.calculate_kpi_usecase import (
    CalculateKpiUseCase,
)
from src.kpi_b2b.kpi_dashboard.dtos.kpi_report_dto import KpiReportDto
from src.shared.dtos.audit_dtos import SecurityAuditEvent
from src.shared.enums.audit_severity_enum import AuditSeverityEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.logging.audit_logger import AuditLogger
from src.shared.security.user_context import UserContext


class KpiQueryFacade(ABC):
    @abstractmethod
    def calculate_oee(self, sim_id: str, ctx: UserContext) -> KpiReportDto:
        pass


class KpiQueryFacadeImpl(KpiQueryFacade):
    def __init__(self, calculate_kpi_uc: CalculateKpiUseCase):
        self._calculate_kpi_uc = calculate_kpi_uc
        self._audit_logger = AuditLogger()

    def calculate_oee(self, sim_id: str, ctx: UserContext) -> KpiReportDto:
        # Guard 1: 멀티테넌시 권한 검증 (Tenant Isolation)
        if not ctx.company_id or ctx.company_id == "UNAUTHORIZED_TENANT":
            # GTS 4.2 Non-blocking 감사 로깅 정책 적용
            audit_event = SecurityAuditEvent(
                action="ACCESS_DENIED_KPI_DASHBOARD",
                target=f"Simulation ID: {sim_id}",
                severity=AuditSeverityEnum.CRITICAL,
                user_ctx=ctx,
            )
            self._audit_logger.log_security_event(audit_event)

            raise BaseSystemException(
                error_code="ERR_KPI_ISOLATION_VIOLATION",
                message="해당 시뮬레이션 결과에 접근할 권한이 없습니다.",
                status_code=403,
            )

        # 2. UseCase로 하향 위임
        return self._calculate_kpi_uc.execute(sim_id=sim_id, company_id=ctx.company_id)
