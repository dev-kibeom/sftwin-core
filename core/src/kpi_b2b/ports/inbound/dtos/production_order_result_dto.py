from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionOrderResultDto:
    order_id: str
    packml_state: str
    factory_phase: str
    remaining_material_stock: float
