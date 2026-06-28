from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

_TRANSITIONS = {
    "접수": {"작업중"},
    "작업중": {"완료"},
    "완료": {"출고"},
    "출고": set(),
}
VALID_STATUSES = set(_TRANSITIONS.keys())


@dataclass
class MaintenancePart:
    part_name: str
    quantity: int
    unit_price: float
    amount: float
    id: Optional[int] = None
    maintenance_id: Optional[int] = None
    product_id: Optional[int] = None


@dataclass
class Payment:
    amount: float
    payment_date: datetime
    id: Optional[int] = None
    maintenance_id: Optional[int] = None
    memo: Optional[str] = None


@dataclass
class MaintenanceOrder:
    customer_id: int
    received_date: datetime
    status: str = "접수"
    machine_type: Optional[str] = None
    machine_number: Optional[str] = None
    symptom: Optional[str] = None
    description: Optional[str] = None
    total_amount: float = 0
    estimate_id: Optional[int] = None
    completed_date: Optional[datetime] = None
    released_date: Optional[datetime] = None
    id: Optional[int] = None
    parts: List[MaintenancePart] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)

    def transition(self, new_status: str):
        allowed = _TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"'{self.status}'에서 '{new_status}'로 변경할 수 없습니다. "
                f"가능: {', '.join(allowed) or '없음'}"
            )
        self.status = new_status
        if new_status == "완료" and not self.completed_date:
            self.completed_date = datetime.now()
        if new_status == "출고" and not self.released_date:
            self.released_date = datetime.now()

    def receivable(self) -> float:
        return max(0.0, round((self.total_amount or 0) - sum(p.amount for p in self.payments), 2))
