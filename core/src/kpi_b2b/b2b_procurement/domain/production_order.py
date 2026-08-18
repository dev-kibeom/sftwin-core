import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from kpi_b2b.b2b_procurement.application.process_production_order.production_order_request_dto import (
    ProductionOrderRequestDto,
)
from kpi_b2b.b2b_procurement.domain.enums.factory_phase_enum import FactoryPhaseEnum
from shared.enums.packml_state_enum import PackMLState


@dataclass
class ProductionOrder:
    order_id: str
    product_code: str
    target_quantity: int
    company_id: str
    factory_phase: FactoryPhaseEnum
    packml_state: PackMLState = PackMLState.IDLE
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def create_order(
        cls, dto: ProductionOrderRequestDto, company_id: str
    ) -> "ProductionOrder":
        """발주 요청 DTO와 company_id를 기반으로 도메인 엔티티 생성 및 불변식 검증"""
        if dto.target_quantity <= 0:
            raise ValueError("Target order quantity must be greater than zero.")

        if not company_id or not company_id.strip():
            raise ValueError(
                "Valid company_id is required to create a production order."
            )

        generated_order_id = dto.order_id or f"ORD-{uuid.uuid4().hex[:8].upper()}"

        return cls(
            order_id=generated_order_id,
            product_code=dto.product_code,
            target_quantity=dto.target_quantity,
            company_id=company_id,
            factory_phase=FactoryPhaseEnum(dto.factory_phase),
            packml_state=PackMLState.IDLE,
        )

    def transition_to_starting(self) -> PackMLState:
        if self.packml_state not in (PackMLState.IDLE, PackMLState.STOPPED):
            raise ValueError(
                f"Cannot transition to STARTING from state {self.packml_state.value}"
            )
        self.packml_state = PackMLState.STARTING
        return self.packml_state

    def transition_to_execute(self) -> PackMLState:
        if self.packml_state != PackMLState.STARTING:
            raise ValueError(
                f"Cannot transition to EXECUTE from state {self.packml_state.value}"
            )
        self.packml_state = PackMLState.EXECUTE
        return self.packml_state
