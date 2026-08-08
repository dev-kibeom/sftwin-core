"""
@file generate_quote_usecase.py
@description 견적 생성 및 외부 마켓플레이스 연동, 예외 검증을 제어하는 유즈케이스
"""

from typing import Any

from src.kpi_b2b.b2b_procurement.adapters.base_b2b_marketplace_port import (
    BaseB2bMarketplacePort,
)
from src.kpi_b2b.b2b_procurement.domain.b2b_quote import B2bQuote
from src.kpi_b2b.b2b_procurement.dtos.b2b_quote_dto import B2bQuoteDto
from src.shared.dtos.log_dtos import LogContext
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.logging.global_system_logger import GlobalSystemLogger


class GenerateQuoteUseCase:
    def __init__(
        self,
        b2b_adapter: BaseB2bMarketplacePort,
        mysql_repo: Any,
        logger: GlobalSystemLogger | None = None,
    ):
        self._b2b_adapter = b2b_adapter
        self._mysql_repo = mysql_repo
        self._logger = logger or GlobalSystemLogger(
            component_name="B2B_GenerateQuote_UseCase"
        )

    def execute(self, asset_ids: list[str], company_id: str) -> B2bQuoteDto:
        log_ctx = LogContext(context={"asset_ids": asset_ids, "company_id": company_id})
        self._logger.info(
            "Initiating Turnkey Quote Request to B2B Marketplace.", log_ctx
        )

        # Guard 2: 외부 통신 / 타임아웃 예외 처리
        try:
            b2b_response = self._b2b_adapter.request_turnkey_quote(asset_ids)
        except Exception as e:
            log_ctx.exc = e
            self._logger.error("B2B API Timeout or Connection Error.", log_ctx)
            raise BaseSystemException(
                error_code="ERR_B2B_API_FAILURE",
                message="B2B 마켓플레이스 공급망 연결이 지연되고 있습니다.",
                status_code=502,
            )

        # Guard 3: 스키마 유효성 검증 (필수 필드 누락 및 타입 에러 방어)
        if (
            "total_estimated_price" not in b2b_response
            or "delivery_days_estimated" not in b2b_response
        ):
            self._logger.warn(
                "Invalid quote schema returned from Marketplace: missing fields.",
                log_ctx,
            )
            raise BaseSystemException(
                error_code="ERR_B2B_INVALID_QUOTE",
                message="비정상적인 견적 응답입니다. 수동 확인이 필요합니다.",
                status_code=422,
            )

        try:
            total_price = float(b2b_response["total_estimated_price"])
            delivery_days = int(b2b_response["delivery_days_estimated"])
        except Exception as e:
            log_ctx.exc = e
            self._logger.warn(
                "Invalid quote schema returned from Marketplace.", log_ctx
            )
            raise BaseSystemException(
                error_code="ERR_B2B_INVALID_QUOTE",
                message="비정상적인 견적 응답입니다. 수동 확인이 필요합니다.",
                status_code=422,
            )

        # 도메인 엔티티 인스턴스화 (REQUESTED 상태 강제 할당)
        quote_entity = B2bQuote.create_new_quote(
            assets=asset_ids, total_price=total_price, days=delivery_days
        )

        # MySQL DB 영속화 예외 가드
        try:
            if self._mysql_repo:
                self._mysql_repo.save(quote_entity)
        except Exception as e:
            log_ctx.exc = e
            self._logger.error(
                "Database persistence failed during quote generation.", log_ctx
            )
            raise BaseSystemException(
                error_code="ERR_COMMON_INTERNAL_ERROR",
                message="시스템 내부 장애가 발생했습니다. 잠시 후 다시 시도해주세요.",
                status_code=500,
            )

        self._logger.info(
            f"Successfully generated turnkey quote: {quote_entity.quote_id}", log_ctx
        )

        return B2bQuoteDto(
            quote_id=quote_entity.quote_id,
            total_estimated_price=quote_entity.total_estimated_price,
            status=quote_entity.status.value,
            delivery_days_estimated=quote_entity.delivery_days_estimated,
        )
