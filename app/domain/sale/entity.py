from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class SaleItem:
    product_name: str
    total_amount: float = 0
    loan_amount: float = 0
    self_pay_amount: float = 0
    id: Optional[int] = None
    sale_id: Optional[int] = None
    model_name: Optional[str] = None
    product_code: Optional[str] = None
    loan_code: Optional[str] = None
    memo: Optional[str] = None


@dataclass
class Sale:
    sale_date: datetime
    customer_id: int
    id: Optional[int] = None
    memo: Optional[str] = None
    machine_category: Optional[str] = None
    items: List[SaleItem] = field(default_factory=list)
