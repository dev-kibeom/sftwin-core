from kpi_b2b.b2b_procurement.domain.b2b_quote import B2bQuote
from kpi_b2b.ports.inbound.dtos.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class GenerateQuoteUseCase:
    def __init__(
        self,
        command_repo: IProcurementCommandRepository,
        system_logger: GlobalSystemLogger | None = None,
    ):
        self._command_repo = command_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="GenerateQuoteUseCase"
        )

    @require_user_context
    def execute(self, asset_ids: list[str], ctx: UserContext) -> B2bQuoteDto:
        log_ctx = LogContext(
            trace_id=getattr(ctx, "trace_id", "TRC-B2B-QUOTE"),
            context={"asset_ids": asset_ids, "company_id": ctx.company_id},
        )

        try:
            b2b_response = self._command_repo.request_turnkey_quote(asset_ids)
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error("B2B API Timeout or Connection Error.", log_ctx)
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_B2B_API_FAILURE,
                message="B2B 마켓플레이스 공급망 연결이 지연되고 있습니다.",
                status_code=502,
            ) from e

        if (
            "total_estimated_price" not in b2b_response
            or "delivery_days_estimated" not in b2b_response
        ):
            self._system_logger.warn(
                "Invalid quote schema returned from Marketplace: missing fields.",
                log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_B2B_INVALID_QUOTE,
                message="비정상적인 견적 응답입니다. 수동 확인이 필요합니다.",
                status_code=422,
            )

        try:
            total_price = float(b2b_response["total_estimated_price"])
            delivery_days = int(b2b_response["delivery_days_estimated"])
        except (ValueError, TypeError) as e:
            log_ctx.exc = e
            self._system_logger.warn(
                "Invalid quote numeric format from Marketplace.", log_ctx
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_B2B_INVALID_QUOTE,
                message="비정상적인 견적 응답입니다. 수동 확인이 필요합니다.",
                status_code=422,
            ) from e

        try:
            quote_entity = B2bQuote.create_new_quote(
                assets=asset_ids, total_price=total_price, days=delivery_days
            )
        except ValueError as e:
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
                message=str(e),
                status_code=400,
            ) from e

        try:
            self._command_repo.save_quote(quote_entity)
        except Exception as e:
            log_ctx.exc = e
            self._system_logger.error(
                "Database persistence failed during quote generation.", log_ctx
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INTERNAL_ERROR,
                message="시스템 내부 장애가 발생했습니다. 잠시 후 다시 시도해주세요.",
                status_code=500,
            ) from e

        self._system_logger.info(
            f"Successfully generated turnkey quote: {quote_entity.quote_id}", log_ctx
        )

        return B2bQuoteDto(
            quote_id=quote_entity.quote_id,
            total_estimated_price=quote_entity.total_estimated_price,
            status=quote_entity.status.value,
            delivery_days_estimated=quote_entity.delivery_days_estimated,
        )
