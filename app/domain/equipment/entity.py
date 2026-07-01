from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Equipment:
    id: Optional[int] = None
    customer_id: Optional[int] = None
    chassis_number: Optional[str] = None
    machine_type: Optional[str] = None
    model_name: Optional[str] = None
    purchase_date: Optional[datetime] = None
    memo: Optional[str] = None
