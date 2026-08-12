"""
@file production_order_dto.py
@description 생산 발주 요청 및 가동 시작 응답 유즈케이스 전용 DTO
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ProductionOrderRequestDto:
    product_code: str
    target_quantity: int
    factory_phase: str  # KAMP_BASELINE or FMS_OPTIMIZED


@dataclass
class ProductionOrderResultDto:
    order_id: str
    packml_state: str
    factory_phase: str
    remaining_material_stock: float
    is_real_to_sim_passed: bool
    validation_details: dict[str, Any] | None = None
