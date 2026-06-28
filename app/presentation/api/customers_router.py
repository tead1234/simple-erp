from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from typing import Optional
from sqlalchemy.orm import Session
from app.application.customer_service import CustomerService, get_customer_service
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/customers", tags=["customers"])


class CustomerIn(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    memo: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("고객명을 입력하세요")
        return v


@router.get("")
def list_customers(q: str = Query(""), svc: CustomerService = Depends(get_customer_service)):
    return [{"id": c.id, "name": c.name, "phone": c.phone, "address": c.address, "memo": c.memo}
            for c in svc.list(q)]


@router.post("", status_code=201)
def create_customer(data: CustomerIn, svc: CustomerService = Depends(get_customer_service), db: Session = Depends(get_db)):
    c = svc.create(**data.model_dump())
    db.commit()
    return {"id": c.id, "name": c.name}


@router.patch("/{customer_id}")
def update_customer(customer_id: int, data: CustomerIn, svc: CustomerService = Depends(get_customer_service), db: Session = Depends(get_db)):
    c = svc.update(customer_id, **data.model_dump())
    db.commit()
    return {"id": c.id, "name": c.name}


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, svc: CustomerService = Depends(get_customer_service), db: Session = Depends(get_db)):
    svc.delete(customer_id)
    db.commit()
