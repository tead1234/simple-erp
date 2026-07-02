from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.application.maintenance_service import MaintenanceService, get_maintenance_service
from app.domain.maintenance.entity import VALID_STATUSES
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


class MaintenanceIn(BaseModel):
    received_date: str
    customer_id: Optional[int] = None
    customer_name: str
    machine_type: Optional[str] = None
    machine_number: Optional[str] = None
    symptom: Optional[str] = None
    estimate_id: Optional[int] = None

    @field_validator("received_date")
    @classmethod
    def valid_date(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("날짜 형식이 올바르지 않습니다")
        return v


class MaintenanceUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None
    total_amount: Optional[float] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"유효하지 않은 상태값: {v}")
        return v

    @field_validator("total_amount")
    @classmethod
    def non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("수리금액은 0 이상이어야 합니다")
        return v


class PartIn(BaseModel):
    product_id: int
    quantity: int = 1
    unit_price: float = 0


class CancelIn(BaseModel):
    confirmed_refund: bool = False


class PaymentIn(BaseModel):
    amount: float
    payment_date: str
    memo: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("입금액은 0보다 커야 합니다")
        return v

    @field_validator("payment_date")
    @classmethod
    def valid_date(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("날짜 형식이 올바르지 않습니다")
        return v


@router.get("")
def list_maintenance(status: Optional[str] = Query(None), q: Optional[str] = Query(None),
                      svc: MaintenanceService = Depends(get_maintenance_service)):
    return svc.list(status, q)


@router.post("", status_code=201)
def create_maintenance(data: MaintenanceIn, svc: MaintenanceService = Depends(get_maintenance_service), db: Session = Depends(get_db)):
    result = svc.create(
        received_date=data.received_date, customer_name=data.customer_name,
        customer_id=data.customer_id, machine_type=data.machine_type,
        machine_number=data.machine_number, symptom=data.symptom, estimate_id=data.estimate_id,
    )
    db.commit()
    return result


@router.get("/{order_id}")
def get_maintenance(order_id: int, svc: MaintenanceService = Depends(get_maintenance_service)):
    return svc.get(order_id)


@router.patch("/{order_id}")
def update_maintenance(order_id: int, data: MaintenanceUpdate, svc: MaintenanceService = Depends(get_maintenance_service), db: Session = Depends(get_db)):
    result = svc.update(order_id, data.status, data.description, data.total_amount)
    db.commit()
    return result


@router.post("/{order_id}/parts", status_code=201)
def add_part(order_id: int, data: PartIn, svc: MaintenanceService = Depends(get_maintenance_service), db: Session = Depends(get_db)):
    result = svc.add_part(order_id, data.product_id, data.quantity, data.unit_price)
    db.commit()
    return result


@router.delete("/{order_id}/parts/{part_id}", status_code=204)
def delete_part(order_id: int, part_id: int, svc: MaintenanceService = Depends(get_maintenance_service), db: Session = Depends(get_db)):
    svc.delete_part(order_id, part_id)
    db.commit()


@router.post("/{order_id}/payments", status_code=201)
def add_payment(order_id: int, data: PaymentIn, svc: MaintenanceService = Depends(get_maintenance_service), db: Session = Depends(get_db)):
    result = svc.add_payment(order_id, data.amount, data.payment_date, data.memo)
    db.commit()
    return result


@router.post("/{order_id}/cancel")
def cancel_maintenance(order_id: int, data: CancelIn, svc: MaintenanceService = Depends(get_maintenance_service), db: Session = Depends(get_db)):
    result = svc.cancel(order_id, data.confirmed_refund)
    db.commit()
    return result
