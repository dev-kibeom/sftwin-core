"""
@file procurement_command_facade.py
@description B2B 발주 및 상담 세션 생성 파사드 (멱등성 보장 및 유즈케이스 제어)
"""

from abc import ABC, abstractmethod

from src.kpi_b2b.b2b_procurement.application.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from src.kpi_b2b.b2b_procurement.dtos.b2b_quote_dto import B2bQuoteDto
from src.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from src.shared.dtos.log_dtos import LogContext
from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext


class ProcurementCommandFacade(ABC):
    @abstractmethod
    def generate_quote(
        self, asset_ids: list[str], idempotency_key: str, ctx: UserContext
    ) -> B2bQuoteDto:
        pass


class ProcurementCommandFacadeImpl(ProcurementCommandFacade):
    def __init__(
        self, generate_quote_uc: GenerateQuoteUseCase, redis_adapter: RedisCacheAdapter
    ):
        self._generate_quote_uc = generate_quote_uc
        self._redis_adapter = redis_adapter
        self._logger = GlobalSystemLogger()
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
