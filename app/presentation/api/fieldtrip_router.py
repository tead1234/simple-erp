from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.application.fieldtrip_service import FieldTripService, get_fieldtrip_service
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/fieldtrips", tags=["fieldtrip"])


class FieldTripIn(BaseModel):
    customer_id: int
    scheduled_date: str
    purpose: Optional[str] = None


class FieldTripUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None


@router.get("")
def list_fieldtrips(status: Optional[str] = Query(None), svc: FieldTripService = Depends(get_fieldtrip_service)):
    return svc.list(status)


@router.post("", status_code=201)
def create_fieldtrip(data: FieldTripIn, svc: FieldTripService = Depends(get_fieldtrip_service), db: Session = Depends(get_db)):
    result = svc.create(data.customer_id, data.scheduled_date, data.purpose)
    db.commit()
    return result


@router.patch("/{trip_id}")
def update_fieldtrip(trip_id: int, data: FieldTripUpdate, svc: FieldTripService = Depends(get_fieldtrip_service), db: Session = Depends(get_db)):
    result = svc.update(trip_id, data.status, data.result)
    db.commit()
    return result
