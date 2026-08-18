from dataclasses import dataclass


@dataclass
class MaterialInventory:
    """원자재 재고 관리 도메인 엔티티"""

    material_code: str
    available_stock: float
    unit_per_product: float

    def __post_init__(self) -> None:
        if not self.material_code or not self.material_code.strip():
            raise ValueError("Valid material_code is required.")
        if self.available_stock < 0:
            raise ValueError("Available stock cannot be negative.")
        if self.unit_per_product <= 0:
            raise ValueError("Unit per product consumption must be positive.")

    def check_and_consume(self, order_quantity: int) -> float:
        if order_quantity <= 0:
            raise ValueError("Order quantity must be greater than zero.")

        required_stock = order_quantity * self.unit_per_product
        if self.available_stock < required_stock:
            raise ValueError(
                f"Insufficient material stock for '{self.material_code}'. "
                f"Required: {required_stock}, Available: {self.available_stock}"
            )

        self.available_stock -= required_stock
        return self.available_stock
