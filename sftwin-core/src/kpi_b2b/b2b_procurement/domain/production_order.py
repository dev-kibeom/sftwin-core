"""
@file production_order.py
@description 시뮬레이션 공장 생산 투입(생산 발주)을 처리하는 도메인 엔티티 및 PackML 상태 전환 규칙
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from src.shared.enums.packml_state_enum import PackMLStateEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes


class FactoryPhaseEnum(str, Enum):
    KAMP_BASELINE = "KAMP_BASELINE"  # FMS 도입 전 (Real-to-Sim 검증 단계)
    FMS_OPTIMIZED = "FMS_OPTIMIZED"  # FMS 도입 후 (스마트팩토리 가동 단계)


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
        cls,
        product_code: str,
        target_quantity: int,
        company_id: str,
        factory_phase: FactoryPhaseEnum,
    ) -> "ProductionOrder":
        if target_quantity <= 0:
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="Target order quantity must be greater than zero.",
                status_code=400,
            )

        return cls(
            order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            product_code=product_code,
            target_quantity=target_quantity,
            company_id=company_id,
            factory_phase=factory_phase,
            packml_state=PackMLStateEnum.IDLE,
        )

    def transition_to_starting(self) -> PackMLStateEnum:
        if self.packml_state not in (PackMLStateEnum.IDLE, PackMLStateEnum.STOPPED):
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message=f"Cannot transition to STARTING from state {self.packml_state.value}",
                status_code=422,
            )
        self.packml_state = PackMLStateEnum.STARTING
        return self.packml_state

    def transition_to_execute(self) -> PackMLStateEnum:
        if self.packml_state != PackMLStateEnum.STARTING:
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message=f"Cannot transition to EXECUTE from state {self.packml_state.value}",
                status_code=422,
            )
        self.packml_state = PackMLStateEnum.EXECUTE
        return self.packml_state
