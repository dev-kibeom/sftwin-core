from dataclasses import dataclass


@dataclass
class MaterialInventory:
    material_code: str
    available_stock: float
    unit_per_product: float

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
