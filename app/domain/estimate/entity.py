from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class EstimateItem:
    model_name: str
    quantity: int = 1
    unit_price: float = 0
    amount: float = 0
    vat: float = 0
    id: Optional[int] = None
    estimate_id: Optional[int] = None
    item_number: Optional[int] = None
    region: Optional[str] = None
    spec: Optional[str] = None
    product_id: Optional[int] = None

    @property
    def unit_price_with_vat(self) -> float:
        return round(self.unit_price * 1.1, 2)


@dataclass
class Estimate:
    contractor_name: str
    estimate_date: datetime
    subtotal: float = 0
    vat_amount: float = 0
    total_amount: float = 0
    status: str = "작성"
    id: Optional[int] = None
    customer_id: Optional[int] = None
    memo: Optional[str] = None
    items: List[EstimateItem] = field(default_factory=list)

    def confirm(self):
        if self.status != "작성":
            raise ValueError("작성 상태의 견적서만 확정할 수 있습니다")
        self.status = "확정"

    def cancel(self):
        if self.status == "취소":
            raise ValueError("이미 취소된 견적서입니다")
        self.status = "취소"
