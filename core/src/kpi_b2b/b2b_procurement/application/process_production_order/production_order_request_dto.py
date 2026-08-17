from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionOrderRequestDto:
    product_code: str
    target_quantity: int
    factory_phase: str
    order_id: str | None = None
