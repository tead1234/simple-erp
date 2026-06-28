from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FieldTrip:
    customer_id: int
    scheduled_date: datetime
    id: Optional[int] = None
    purpose: Optional[str] = None
    status: str = "예정"  # 예정 / 완료 / 취소
    result: Optional[str] = None
