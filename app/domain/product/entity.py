from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    name: str
    id: Optional[int] = None
    code: Optional[str] = None
    old_code: Optional[str] = None
    category: Optional[str] = None
    model: Optional[str] = None
    stock_quantity: int = 0
    min_stock_quantity: int = 0
    unit_price: float = 0
    dealer_price: float = 0
    center_price: float = 0
    consumer_price: float = 0

    @property
    def is_low_stock(self) -> bool:
        # 엑셀 이관 재고에 수량 데이터가 없어 임시로 꺼둠. 재고수량 재입력 후 원복: self.stock_quantity <= self.min_stock_quantity
        return False

    def deduct(self):
        if self.stock_quantity <= 0:
            raise ValueError(f"재고 부족 (현재: {self.stock_quantity})")
        self.stock_quantity -= 1
