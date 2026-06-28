from dataclasses import dataclass
from typing import Optional


@dataclass
class CompanySettings:
    id: Optional[int] = None
    registration_number: Optional[str] = None
    company_name: Optional[str] = None
    owner_name: Optional[str] = None
    address: Optional[str] = None
    business_type: Optional[str] = None
    business_category: Optional[str] = None
    phone: Optional[str] = None
