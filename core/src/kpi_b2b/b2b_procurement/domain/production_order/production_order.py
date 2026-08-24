import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.enums.packml_state_enum import PackMLState

from .factory_phase_enum import FactoryPhase


@dataclass
class ProductionOrder:
    order_id: str
    product_code: str
    target_quantity: int
    company_id: str
    factory_phase: FactoryPhase
    packml_state: PackMLState = PackMLState.IDLE
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.order_id or not self.order_id.strip():
            raise ValueError("Valid order_id is required.")
        if not self.product_code or not self.product_code.strip():
            raise ValueError("Valid product_code is required.")
        if self.target_quantity <= 0:
            raise ValueError("Target order quantity must be greater than zero.")
        if not self.company_id or not self.company_id.strip():
            raise ValueError("Valid company_id is required.")
        if not isinstance(self.factory_phase, FactoryPhase):
            raise ValueError(
                f"factory_phase must be a valid FactoryPhase enum. Got: {self.factory_phase}"
            )

    @classmethod
    def create(
        cls,
        product_code: str,
        target_quantity: int,
        company_id: str,
        factory_phase: FactoryPhase,
        order_id: str | None = None,
    ) -> "ProductionOrder":
        return cls(
            order_id=order_id or f"ORD-{uuid.uuid4().hex[:8].upper()}",
            product_code=product_code,
            target_quantity=target_quantity,
            company_id=company_id,
            factory_phase=factory_phase,
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
