from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.application.customer_service import CustomerService, get_customer_service
from app.infrastructure.database.session import get_db
from app.infrastructure.database.orm import (
    Sale as ORM_Sale, SaleItem as ORM_SaleItem,
    MaintenanceOrder as ORM_Maintenance, Payment as ORM_Payment,
    FieldTrip as ORM_FieldTrip, Equipment as ORM_Equipment,
)

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


class ReceivableMemoIn(BaseModel):
    memo: Optional[str] = None


@router.patch("/{customer_id}/receivable-memo")
def update_receivable_memo(customer_id: int, data: ReceivableMemoIn, svc: CustomerService = Depends(get_customer_service), db: Session = Depends(get_db)):
    svc.update_receivable_memo(customer_id, data.memo)
    db.commit()
    return {"id": customer_id}


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, svc: CustomerService = Depends(get_customer_service), db: Session = Depends(get_db)):
    svc.delete(customer_id)
    db.commit()


@router.get("/{customer_id}/detail")
def customer_detail(customer_id: int, svc: CustomerService = Depends(get_customer_service), db: Session = Depends(get_db)):
    customers = svc.list("")
    customer = next((c for c in customers if c.id == customer_id), None)
    if not customer:
        from fastapi import HTTPException
        raise HTTPException(404, "고객을 찾을 수 없습니다")

    equipment = db.query(ORM_Equipment).filter(ORM_Equipment.customer_id == customer_id).all()

    sales_raw = db.query(ORM_Sale).filter(ORM_Sale.customer_id == customer_id).order_by(ORM_Sale.sale_date.desc()).all()
    sales = []
    for s in sales_raw:
        items = db.query(ORM_SaleItem).filter(ORM_SaleItem.sale_id == s.id).all()
        sales.append({
            "id": s.id,
            "sale_date": s.sale_date.isoformat() if s.sale_date else None,
            "machine_category": s.machine_category,
            "memo": s.memo,
            "items": [{"product_name": i.product_name, "model_name": i.model_name,
                       "total_amount": i.total_amount, "loan_amount": i.loan_amount,
                       "self_pay_amount": i.self_pay_amount} for i in items],
        })

    maintenances_raw = db.query(ORM_Maintenance).filter(
        ORM_Maintenance.customer_id == customer_id
    ).order_by(ORM_Maintenance.received_date.desc()).all()
    maintenances = []
    total_unpaid = 0.0
    for m in maintenances_raw:
        paid = db.query(func.coalesce(func.sum(ORM_Payment.amount), 0)).filter(
            ORM_Payment.maintenance_id == m.id
        ).scalar() or 0
        unpaid = (m.total_amount or 0) - paid
        if unpaid > 0:
            total_unpaid += unpaid
        maintenances.append({
            "id": m.id,
            "received_date": m.received_date.isoformat() if m.received_date else None,
            "machine_type": m.machine_type, "machine_number": m.machine_number,
            "symptom": m.symptom, "status": m.status,
            "total_amount": m.total_amount or 0, "paid": paid, "unpaid": unpaid,
        })

    field_trips = db.query(ORM_FieldTrip).filter(
        ORM_FieldTrip.customer_id == customer_id
    ).order_by(ORM_FieldTrip.scheduled_date.desc()).all()

    return {
        "customer": {"id": customer.id, "name": customer.name, "phone": customer.phone,
                     "address": customer.address, "memo": customer.memo},
        "equipment": [{"id": e.id, "chassis_number": e.chassis_number, "machine_type": e.machine_type,
                       "model_name": e.model_name,
                       "purchase_date": e.purchase_date.isoformat() if e.purchase_date else None} for e in equipment],
        "sales": sales,
        "maintenances": maintenances,
        "field_trips": [{"id": ft.id,
                         "scheduled_date": ft.scheduled_date.isoformat() if ft.scheduled_date else None,
                         "purpose": ft.purpose, "status": ft.status, "result": ft.result} for ft in field_trips],
        "total_unpaid": total_unpaid,
    }
