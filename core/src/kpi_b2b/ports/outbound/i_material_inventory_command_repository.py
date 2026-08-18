from typing import Protocol

from kpi_b2b.b2b_procurement.domain.production_order.material_inventory import (
    MaterialInventory,
)


class IMaterialInventoryCommandRepository(Protocol):
    """원자재 변경사항 영속화 포트"""

    def update_stock(self, inventory: MaterialInventory) -> None:
        """소진된 재고 상태 영속화"""
        ...
