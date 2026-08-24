from dataclasses import asdict

from kpi_b2b.b2b_procurement.domain.b2b_quote.b2b_quote import B2bQuote
from kpi_b2b.contracts.dtos.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.contracts.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.contracts.ports.outbound.i_quote_idempotency_store import (
    IQuoteIdempotencyStore,
)
from kpi_b2b.contracts.ports.outbound.i_turnkey_quote_gateway import (
    ITurnkeyQuoteGateway,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class GenerateQuoteUseCase:
    """B2B 턴키 견적 요청 및 멱등 캐싱을 처리하는 유스케이스"""

    def __init__(
        self,
        gateway: ITurnkeyQuoteGateway,
        cache_store: IQuoteIdempotencyStore,
        command_repo: IProcurementCommandRepository,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._gateway = gateway
        self._cache_store = cache_store
        self._command_repo = command_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GenerateQuoteUseCase"
        )

    @require_user_context
    def execute(
        self,
        asset_ids: list[str],
        ctx: UserContext,
        idempotency_key: str | None = None,
    ) -> B2bQuoteDto:
        # 1. 입력 인자 조기 검증
        if not asset_ids:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message="At least one asset_id is required to request a turnkey quote.",
            )

        # 2. 멱등성 캐시 확인 (캐시 에러 시 메인 로직 fallback)
        if idempotency_key:
            try:
                cached_data = self._cache_store.find_cached_quote(idempotency_key)
                if cached_data:
                    return B2bQuoteDto(**cached_data)
            except Exception:
                self._system_logger.warn(
                    f"Cache store lookup failed for key '{idempotency_key}'. Proceeding without cache.",
                    extra={"idempotency_key": idempotency_key},
                )

        # 3. 외부 B2B Gateway 연동 (외부 API 호출 및 스키마 검증)
        quote_res_dto = self._gateway.request_turnkey_quote(asset_ids)

        # 4. 도메인 엔티티 생성 (식별자 생성 및 불변식 검증 팩토리 위임)
        try:
            quote_entity = B2bQuote.create(
                asset_ids=asset_ids,
                total_estimated_price=quote_res_dto.total_estimated_price,
                delivery_days_estimated=quote_res_dto.delivery_days_estimated,
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        # 5. 저장소 영속화
        self._command_repo.save_quote(quote_entity)

        result_dto = B2bQuoteDto(
            quote_id=quote_entity.quote_id,
            total_estimated_price=quote_entity.total_estimated_price,
            status=quote_entity.status.value,
            delivery_days_estimated=quote_entity.delivery_days_estimated,
        )

        # 6. 캐시 갱신
        if idempotency_key:
            try:
                self._cache_store.save_cached_quote(
                    idempotency_key=idempotency_key,
                    data=asdict(result_dto),
                )
            except Exception:
                self._system_logger.warn(
                    f"Failed to cache quote result for key '{idempotency_key}'.",
                    extra={"idempotency_key": idempotency_key},
                )

        # 7. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Successfully generated turnkey quote: {quote_entity.quote_id}",
            extra={
                "quote_id": quote_entity.quote_id,
                "asset_count": len(asset_ids),
                "total_price": quote_entity.total_estimated_price,
                "company_id": ctx.company_id,
            },
        )

        return result_dto
