from typing import Protocol

from kpi_b2b.b2b_procurement.domain.production_order.material_inventory import (
    MaterialInventory,
)


class IMaterialInventoryQueryRepository(Protocol):
    """원자재 재고 조회 포트"""

    def get_by_material_code(self, material_code: str) -> MaterialInventory | None:
        """자재 코드로 현재 가용 재고 객체 조회"""
        ...
