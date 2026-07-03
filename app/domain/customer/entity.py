from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    name: str
    id: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    memo: Optional[str] = None
    is_active: bool = True
