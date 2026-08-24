import uuid

from kpi_b2b.b2b_procurement.domain.b2b_quote.b2b_quote import B2bQuote
from kpi_b2b.ports.inbound.dtos.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.ports.outbound.i_quote_idempotency_store import (
    IQuoteIdempotencyStore,
)
from kpi_b2b.ports.outbound.i_turnkey_quote_gateway import (
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
        # 1. 멱등성 캐시 확인 (캐시 장애 시 Fallback)
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

        # 2. 외부 B2B Gateway 연동 (Gateway ACL이 통신/스키마 예외 번역 후 DTO 반환 및 상위 전파)
        quote_res_dto = self._gateway.request_turnkey_quote(asset_ids)

        # 3. 도메인 엔티티 생성 및 불변식 검증
        try:
            quote_entity = B2bQuote(
                quote_id=f"QT-{uuid.uuid4()}",
                asset_ids=tuple(asset_ids),
                total_estimated_price=quote_res_dto.total_estimated_price,
                delivery_days_estimated=quote_res_dto.delivery_days_estimated,
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        # 4. 저장소 영속화 (DB 예외는 Repository Adapter에서 처리되어 상위 전파)
        self._command_repo.save_quote(quote_entity)

        result_dto = B2bQuoteDto(
            quote_id=quote_entity.quote_id,
            total_estimated_price=quote_entity.total_estimated_price,
            status=quote_entity.status.value,
            delivery_days_estimated=quote_entity.delivery_days_estimated,
        )

        # 5. 캐시 갱신
        if idempotency_key:
            try:
                self._cache_store.save_cached_quote(
                    idempotency_key=idempotency_key,
                    data={
                        "quote_id": result_dto.quote_id,
                        "total_estimated_price": result_dto.total_estimated_price,
                        "status": result_dto.status,
                        "delivery_days_estimated": result_dto.delivery_days_estimated,
                    },
                )
            except Exception:
                self._system_logger.warn(
                    f"Failed to cache quote result for key '{idempotency_key}'.",
                    extra={"idempotency_key": idempotency_key},
                )

        # 6. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Successfully generated turnkey quote: {quote_entity.quote_id}",
            extra={
                "quote_id": quote_entity.quote_id,
                "asset_count": len(asset_ids),
                "total_price": quote_entity.total_estimated_price,
            },
        )

        return result_dto
