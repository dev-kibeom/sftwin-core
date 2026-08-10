"""
@file procurement_command_facade.py
@description RbacAuthorizationManager를 연동한 B2B 및 상담 세션 커맨드 파사드
"""

from abc import ABC, abstractmethod
from typing import Any

from src.kpi_b2b.b2b_procurement.application.generate_quote.b2b_quote_dto import (
    B2bQuoteDto,
)
from src.kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from src.kpi_b2b.b2b_procurement.application.layout_mirroring.layout_mirroring_usecase import (
    LayoutMirroringUseCase,
)
from src.kpi_b2b.b2b_procurement.application.layout_mirroring.session_data_dto import (
    SessionDataDto,
)
from src.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from src.shared.dtos.log_dtos import LogContext
from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.rbac_authorization_manager import RbacAuthorizationManager
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
        rbac_manager: RbacAuthorizationManager,
        baseline_repo: Any = None,
    ):
        self._generate_quote_uc = generate_quote_uc
        self._mirroring_uc = mirroring_uc
        self._redis_adapter = redis_adapter
        self._rbac_manager = rbac_manager
        self._baseline_repo = baseline_repo
        self._logger = GlobalSystemLogger(component_name="Procurement_Facade")

    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto:
        log_ctx = LogContext(
            context={"idempotency_key": idempotency_key, "user_id": ctx.user_id}
        )

        # Guard 1: 멱등성 검증
        if idempotency_key:
            cached_data = self._redis_adapter.get_cached_quote(idempotency_key)
            if cached_data:
                self._logger.info(
                    "Idempotency Cache Hit. Returning cached quote.", log_ctx
                )
                return B2bQuoteDto(**cached_data)

        self._logger.info("Cache Miss. Proceeding to generate new quote.", log_ctx)
        quote_dto = self._generate_quote_uc.execute(
            asset_ids=asset_ids, company_id=ctx.company_id
        )

        if idempotency_key:
            self._redis_adapter.set_cached_quote(
                idempotency_key, quote_dto.__dict__, 86400
            )

        return quote_dto

    def create_expert_session(
        self, baseline_id: str, ctx: UserContext
    ) -> SessionDataDto:
        # 실제 DB에서 Baseline 도면 소유주 조회
        target_company_id = (
            self._baseline_repo.get_owner(baseline_id)
            if hasattr(self._baseline_repo, "get_owner")
            else "UNAUTHORIZED_TENANT"
        )

        # 전역 보안 모듈에 위임 (실패 시 403 예외 및 CRITICAL 로깅 자동 수행)
        self._rbac_manager.validate_company_isolation(
            user_ctx=ctx,
            target_company_id=target_company_id,
            target_resource=f"BASELINE:{baseline_id}",
        )

        self._logger.info(
            f"Authorized session creation for baseline {baseline_id} by {ctx.company_id}"
        )
        return self._mirroring_uc.execute(
            baseline_id=baseline_id, company_id=ctx.company_id
        )
