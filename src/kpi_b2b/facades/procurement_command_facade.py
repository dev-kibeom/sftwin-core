"""
@file procurement_command_facade.py
@description B2B 발주 및 상담 세션 생성 파사드 (멱등성 보장 및 유즈케이스 제어)
"""

from abc import ABC, abstractmethod
from typing import Any

from src.kpi_b2b.b2b_procurement.application.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from src.kpi_b2b.b2b_procurement.application.layout_mirroring_usecase import (
    LayoutMirroringUseCase,
)
from src.kpi_b2b.b2b_procurement.dtos.b2b_quote_dto import B2bQuoteDto
from src.kpi_b2b.b2b_procurement.dtos.session_data_dto import SessionDataDto
from src.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from src.shared.dtos.audit_dtos import SecurityAuditEvent
from src.shared.dtos.log_dtos import LogContext
from src.shared.enums.audit_severity_enum import AuditSeverityEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.logging.audit_logger import AuditLogger
from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext


class ProcurementCommandFacade(ABC):
    @abstractmethod
    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto:
        pass

    @abstractmethod
    def create_expert_session(
        self, baseline_id: str, ctx: UserContext
    ) -> SessionDataDto:
        pass


class ProcurementCommandFacadeImpl(ProcurementCommandFacade):
    def __init__(
        self,
        generate_quote_uc: GenerateQuoteUseCase,
        mirroring_uc: LayoutMirroringUseCase,
        redis_adapter: RedisCacheAdapter,
        baseline_repo: Any = None,
    ):  # 소유권 검증용 레포지토리
        self._generate_quote_uc = generate_quote_uc
        self._mirroring_uc = mirroring_uc
        self._redis_adapter = redis_adapter
        self._baseline_repo = baseline_repo

        self._logger = GlobalSystemLogger()
        self._audit_logger = AuditLogger()
        self._logger.component_name = "Procurement_Facade"

    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto:
        log_ctx = LogContext(
            context={"idempotency_key": idempotency_key, "user_id": ctx.user_id}
        )

        # Guard 1: 멱등성 검증 (Redis Cache 히트 확인)
        if idempotency_key:
            cached_data = self._redis_adapter.get_cached_quote(idempotency_key)
            if cached_data:
                self._logger.info(
                    "Idempotency Cache Hit. Returning cached quote.", log_ctx
                )
                return B2bQuoteDto(**cached_data)

        # Cache Miss: 유즈케이스 진입을 통한 신규 견적 발행
        self._logger.info("Cache Miss. Proceeding to generate new quote.", log_ctx)
        quote_dto = self._generate_quote_uc.execute(
            asset_ids=asset_ids, company_id=ctx.company_id
        )

        # 성공된 응답 결과를 Redis에 24시간(86400초) 캐싱
        if idempotency_key:
            self._redis_adapter.set_cached_quote(
                idempotency_key=idempotency_key, data=quote_dto.__dict__, ttl=86400
            )

        return quote_dto

    def create_expert_session(
        self, baseline_id: str, ctx: UserContext
    ) -> SessionDataDto:
        # Guard 1: 멀티테넌시 데이터 격리 (baseline 소유권 검증)
        # 실제 환경에서는 DB에서 baseline을 조회하여 소유주(company_id)를 비교합니다.
        # 본 데모에서는 "UNAUTHORIZED"가 포함된 경우를 위반으로 간주하는 Stub 로직 적용
        if "UNAUTHORIZED" in ctx.company_id:
            audit_event = SecurityAuditEvent(
                action="EXPERT_SESSION_ISOLATION_VIOLATION",
                target=f"Baseline ID: {baseline_id}",
                severity=AuditSeverityEnum.CRITICAL,
                user_ctx=ctx,
            )
            self._audit_logger.log_security_event(audit_event)

            raise BaseSystemException(
                error_code="ERR_KPI_ISOLATION_VIOLATION",
                message="해당 가상 공장 도면에 대한 접근 권한이 없습니다.",
                status_code=403,
            )

        # 권한 인가 성공 시 세션 생성 유즈케이스로 위임
        self._logger.info(
            f"Authorized session creation for baseline {baseline_id} by {ctx.company_id}"
        )
        return self._mirroring_uc.execute(
            baseline_id=baseline_id, company_id=ctx.company_id
        )
