"""
@file production_order.py
@description 시뮬레이션 공장 생산 투입(생산 발주)을 처리하는 도메인 엔티티 및 PackML 상태 전환 규칙
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from kpi_b2b.b2b_procurement.application.process_production_order.production_order_dto import (
    ProductionOrderRequestDto,
)
from kpi_b2b.b2b_procurement.domain.factory_phase_enum import FactoryPhaseEnum
from shared.context.user_context import UserContext
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.enums.packml_state_enum import PackMLStateEnum
from shared.exceptions.base_exception import BaseSystemException


@dataclass
class ProductionOrder:
    order_id: str
    product_code: str
    target_quantity: int
    company_id: str
    factory_phase: FactoryPhaseEnum
    packml_state: PackMLStateEnum = PackMLStateEnum.IDLE
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def create_order(
        cls, dto: ProductionOrderRequestDto, ctx: UserContext
    ) -> "ProductionOrder":
        """발주 요청 DTO와 인가된 UserContext만을 조합하여 엔티티 생성"""
        if dto.target_quantity <= 0:
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
                message="Target order quantity must be greater than zero.",
                status_code=400,
            )

        if not ctx.company_id or not ctx.company_id.strip():
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_UNAUTHORIZED,
                message="Valid company context is required to create a production order.",
                status_code=401,
            )

        generated_order_id = dto.order_id or f"ORD-{uuid.uuid4().hex[:8].upper()}"

        return cls(
            order_id=generated_order_id,
            product_code=dto.product_code,
            target_quantity=dto.target_quantity,
            company_id=ctx.company_id,
            factory_phase=FactoryPhaseEnum(dto.factory_phase),
            packml_state=PackMLStateEnum.IDLE,
        )

    def transition_to_starting(self) -> PackMLStateEnum:
        if self.packml_state not in (PackMLStateEnum.IDLE, PackMLStateEnum.STOPPED):
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
                message=f"Cannot transition to STARTING from state {self.packml_state.value}",
                status_code=422,
            )
        self.packml_state = PackMLStateEnum.STARTING
        return self.packml_state

    def transition_to_execute(self) -> PackMLStateEnum:
        if self.packml_state != PackMLStateEnum.STARTING:
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
                message=f"Cannot transition to EXECUTE from state {self.packml_state.value}",
                status_code=422,
            )
        self.packml_state = PackMLStateEnum.EXECUTE
        return self.packml_state
