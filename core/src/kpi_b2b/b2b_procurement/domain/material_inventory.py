"""
@file material_inventory.py
@description 생산 발주에 따른 원자재 재고 차감 및 부족 여부 검증 도메인 엔티티
"""

from dataclasses import dataclass

from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException


@dataclass
class MaterialInventory:
    material_code: str
    available_stock: float
    unit_per_product: float

    def check_and_consume(self, order_quantity: int) -> float:
        required_stock = order_quantity * self.unit_per_product
        if self.available_stock < required_stock:
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_COMMON_INVALID_INPUT,
                message=f"Insufficient material stock for '{self.material_code}'. Required: {required_stock}, Available: {self.available_stock}",
                status_code=422,
                details={
                    "material_code": self.material_code,
                    "required": required_stock,
                    "available": self.available_stock,
                },
            )

        self.available_stock -= required_stock
        return self.available_stock
