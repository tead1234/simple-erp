from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    name: str
    id: Optional[int] = None
    code: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: int = 0
    min_stock_quantity: int = 0
    unit_price: float = 0

    @property
    def is_low_stock(self) -> bool:
        return self.stock_quantity <= 1

    def deduct(self):
        if self.stock_quantity <= 0:
            raise ValueError(f"재고 부족 (현재: {self.stock_quantity})")
        self.stock_quantity -= 1
