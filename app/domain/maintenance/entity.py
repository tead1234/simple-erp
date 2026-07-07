from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

_TRANSITIONS = {
    "작업중": {"완료"},
    "완료": {"출고", "작업중"},
    "출고": {"완료"},
}
CANCELLABLE_STATUSES = {"작업중", "완료", "출고"}
VALID_STATUSES = set(_TRANSITIONS.keys()) | {"취소"}


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
class MaintenancePhoto:
    content_type: str
    id: Optional[int] = None
    maintenance_id: Optional[int] = None
    drive_file_id: Optional[str] = None
    created_at: Optional[datetime] = None


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
    status: str = "작업중"
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
    photos: List[MaintenancePhoto] = field(default_factory=list)

    def transition(self, new_status: str):
        allowed = _TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"'{self.status}'에서 '{new_status}'로 변경할 수 없습니다. "
                f"가능: {', '.join(allowed) or '없음'}"
            )
        self.status = new_status
        if new_status == "완료":
            self.completed_date = self.completed_date or datetime.now()
            self.released_date = None  # 출고에서 되돌아온 경우 초기화
        elif new_status == "출고":
            self.released_date = self.released_date or datetime.now()
        elif new_status == "작업중":
            self.completed_date = None
            self.released_date = None

    def cancel(self):
        if self.status not in CANCELLABLE_STATUSES:
            raise ValueError(f"'{self.status}' 상태의 정비는 취소할 수 없습니다")
        self.status = "취소"

    def receivable(self) -> float:
        return max(0.0, round((self.total_amount or 0) - sum(p.amount for p in self.payments), 2))
