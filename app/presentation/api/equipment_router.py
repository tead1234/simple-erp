from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.application.equipment_service import EquipmentService, get_equipment_service
from app.infrastructure.database.session import get_db
from app.infrastructure.database.orm import (
    Equipment as ORM_Equipment, Customer as ORM_Customer,
    MaintenanceOrder as ORM_Maintenance, Payment as ORM_Payment,
    Sale as ORM_Sale, SaleItem as ORM_SaleItem, FieldTrip as ORM_FieldTrip,
)

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


class EquipmentIn(BaseModel):
    customer_id: Optional[int] = None
    chassis_number: Optional[str] = None
    machine_type: Optional[str] = None
    model_name: Optional[str] = None
    purchase_date: Optional[str] = None
    memo: Optional[str] = None


@router.get("")
def list_equipment(svc: EquipmentService = Depends(get_equipment_service)):
    return svc.list()


@router.post("", status_code=201)
def create_equipment(data: EquipmentIn, svc: EquipmentService = Depends(get_equipment_service), db: Session = Depends(get_db)):
    result = svc.create(**data.model_dump())
    db.commit()
    return result


@router.patch("/{eq_id}")
def update_equipment(eq_id: int, data: EquipmentIn, svc: EquipmentService = Depends(get_equipment_service), db: Session = Depends(get_db)):
    result = svc.update(eq_id, **data.model_dump(exclude_none=True))
    db.commit()
    return result


@router.delete("/{eq_id}", status_code=204)
def delete_equipment(eq_id: int, svc: EquipmentService = Depends(get_equipment_service), db: Session = Depends(get_db)):
    svc.delete(eq_id)
    db.commit()


@router.get("/search")
def search_by_chassis(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    equipments = db.query(ORM_Equipment).filter(ORM_Equipment.chassis_number.contains(q)).all()
    results = []
    for eq in equipments:
        customer = db.query(ORM_Customer).filter(ORM_Customer.id == eq.customer_id).first() if eq.customer_id else None

        maintenances = db.query(ORM_Maintenance).filter(
            ORM_Maintenance.machine_number.contains(eq.chassis_number)
        ).order_by(ORM_Maintenance.received_date.desc()).all()

        maintenance_list = []
        total_unpaid = 0.0
        for m in maintenances:
            paid = db.query(func.coalesce(func.sum(ORM_Payment.amount), 0)).filter(
                ORM_Payment.maintenance_id == m.id
            ).scalar() or 0
            unpaid = (m.total_amount or 0) - paid
            if unpaid > 0:
                total_unpaid += unpaid
            maintenance_list.append({
                "id": m.id, "received_date": m.received_date.isoformat() if m.received_date else None,
                "machine_type": m.machine_type, "machine_number": m.machine_number,
                "symptom": m.symptom, "status": m.status,
                "total_amount": m.total_amount or 0, "paid": paid, "unpaid": unpaid,
            })

        sales = []
        field_trips = []
        if customer:
            for s in db.query(ORM_Sale).filter(ORM_Sale.customer_id == customer.id).order_by(ORM_Sale.sale_date.desc()).all():
                items = db.query(ORM_SaleItem).filter(ORM_SaleItem.sale_id == s.id).all()
                sales.append({
                    "id": s.id, "sale_date": s.sale_date.isoformat() if s.sale_date else None,
                    "machine_category": s.machine_category, "memo": s.memo,
                    "items": [{"product_name": i.product_name, "model_name": i.model_name,
                               "total_amount": i.total_amount} for i in items],
                })
            for ft in db.query(ORM_FieldTrip).filter(ORM_FieldTrip.customer_id == customer.id).order_by(ORM_FieldTrip.scheduled_date.desc()).all():
                field_trips.append({
                    "id": ft.id, "scheduled_date": ft.scheduled_date.isoformat() if ft.scheduled_date else None,
                    "purpose": ft.purpose, "status": ft.status, "result": ft.result,
                })

        results.append({
            "equipment": {
                "id": eq.id, "chassis_number": eq.chassis_number,
                "machine_type": eq.machine_type, "model_name": eq.model_name,
                "purchase_date": eq.purchase_date.isoformat() if eq.purchase_date else None,
                "memo": eq.memo,
            },
            "customer": {"id": customer.id, "name": customer.name, "phone": customer.phone} if customer else None,
            "maintenances": maintenance_list,
            "sales": sales,
            "field_trips": field_trips,
            "total_unpaid": total_unpaid,
        })
    return results
