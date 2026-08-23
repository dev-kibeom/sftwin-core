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
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class GenerateQuoteUseCase:
    def __init__(
        self,
        gateway: ITurnkeyQuoteGateway,
        cache_store: IQuoteIdempotencyStore,
        command_repo: IProcurementCommandRepository,
        system_logger: GlobalSystemLogger | None = None,
    ):
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
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-B2B-QUOTE"),
            context={
                "asset_ids": asset_ids,
                "company_id": ctx.company_id,
                "idempotency_key": idempotency_key,
            },
        )
        self._system_logger.debug(f"Executing {self.__class__.__name__}", log_ctx)

        if idempotency_key:
            try:
                cached_data = self._cache_store.find_cached_quote(idempotency_key)
                if cached_data:
                    self._system_logger.debug(
                        f"Idempotent cache hit for key: {idempotency_key}", log_ctx
                    )
                    return B2bQuoteDto(**cached_data)
            except Exception as e:
                log_ctx.exc = e
                self._system_logger.warn(
                    f"Cache store lookup failed for key '{idempotency_key}'. Proceeding without cache.",
                    log_ctx,
                )

        try:
            b2b_response = self._gateway.request_turnkey_quote(asset_ids)
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error("B2B API Timeout or Connection Error.", log_ctx)
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_B2B_API_FAILURE
            ) from e

        if (
            "total_estimated_price" not in b2b_response
            or "delivery_days_estimated" not in b2b_response
        ):
            self._system_logger.warn(
                "Invalid quote schema returned from Marketplace: missing required fields.",
                log_ctx,
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_B2B_INVALID_QUOTE
            )

        try:
            total_price = float(b2b_response["total_estimated_price"])
            delivery_days = int(b2b_response["delivery_days_estimated"])
        except (ValueError, TypeError) as e:
            log_ctx.exc = e
            self._system_logger.warn(
                "Invalid quote numeric format from Marketplace.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_B2B_INVALID_QUOTE
            ) from e

        try:
            quote_entity = B2bQuote(
                quote_id=f"QT-{uuid.uuid4()}",
                asset_ids=tuple(asset_ids),
                total_estimated_price=total_price,
                delivery_days_estimated=delivery_days,
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INVALID_INPUT,
                custom_message=str(e),
            ) from e

        try:
            self._command_repo.save_quote(quote_entity)
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error(
                "Database persistence failed during quote generation.", log_ctx
            )
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_COMMON_INTERNAL_ERROR
            ) from e

        result_dto = B2bQuoteDto(
            quote_id=quote_entity.quote_id,
            total_estimated_price=quote_entity.total_estimated_price,
            status=quote_entity.status.value,
            delivery_days_estimated=quote_entity.delivery_days_estimated,
        )

        if idempotency_key:
            self._cache_store.save_cached_quote(
                idempotency_key=idempotency_key,
                data={
                    "quote_id": result_dto.quote_id,
                    "total_estimated_price": result_dto.total_estimated_price,
                    "status": result_dto.status,
                    "delivery_days_estimated": result_dto.delivery_days_estimated,
                },
            )

        self._system_logger.info(
            f"Successfully generated turnkey quote: {quote_entity.quote_id}", log_ctx
        )
        return result_dto
