"""
@file production_order_dto.py
@description 생산 발주 요청 및 응답 전용 DTO
"""

from dataclasses import dataclass


@dataclass
class ProductionOrderRequestDto:
    product_code: str
    target_quantity: int
    factory_phase: str
    order_id: str | None = None


@dataclass
class ProductionOrderResultDto:
    order_id: str
    packml_state: str
    factory_phase: str
    remaining_material_stock: float
