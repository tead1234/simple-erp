from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.application.estimate_service import EstimateService, get_estimate_service
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/estimates", tags=["estimates"])


class EstimateItemIn(BaseModel):
    region: Optional[str] = None
    model_name: str
    spec: Optional[str] = None
    quantity: int = 1
    unit_price: float = 0

    @field_validator("model_name")
    @classmethod
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError("품목명을 입력하세요")
        return v.strip()


class EstimateIn(BaseModel):
    contractor_name: str
    customer_name: Optional[str] = None
    customer_id: Optional[int] = None
    estimate_date: str
    memo: Optional[str] = None
    items: List[EstimateItemIn]

    @field_validator("estimate_date")
    @classmethod
    def valid_date(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("날짜 형식이 올바르지 않습니다")
        return v

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("품목을 하나 이상 입력하세요")
        return v


@router.get("")
def list_estimates(svc: EstimateService = Depends(get_estimate_service)):
    return svc.list()


@router.post("", status_code=201)
def create_estimate(data: EstimateIn, svc: EstimateService = Depends(get_estimate_service), db: Session = Depends(get_db)):
    result = svc.create(
        contractor_name=data.contractor_name, customer_name=data.customer_name,
        customer_id=data.customer_id, estimate_date=data.estimate_date,
        memo=data.memo, items=[i.model_dump() for i in data.items],
    )
    db.commit()
    return result


@router.get("/{estimate_id}")
def get_estimate(estimate_id: int, svc: EstimateService = Depends(get_estimate_service)):
    return svc.get(estimate_id)


@router.put("/{estimate_id}")
def update_estimate(estimate_id: int, data: EstimateIn, svc: EstimateService = Depends(get_estimate_service), db: Session = Depends(get_db)):
    result = svc.update(
        estimate_id=estimate_id, contractor_name=data.contractor_name,
        customer_name=data.customer_name, customer_id=data.customer_id,
        estimate_date=data.estimate_date, memo=data.memo,
        items=[i.model_dump() for i in data.items],
    )
    db.commit()
    return result


@router.delete("/{estimate_id}", status_code=204)
def delete_estimate(estimate_id: int, svc: EstimateService = Depends(get_estimate_service), db: Session = Depends(get_db)):
    svc.delete(estimate_id)
    db.commit()


@router.post("/{estimate_id}/confirm")
def confirm_estimate(estimate_id: int, svc: EstimateService = Depends(get_estimate_service), db: Session = Depends(get_db)):
    result = svc.confirm(estimate_id)
    db.commit()
    return result


@router.post("/{estimate_id}/cancel")
def cancel_estimate(estimate_id: int, svc: EstimateService = Depends(get_estimate_service), db: Session = Depends(get_db)):
    result = svc.cancel(estimate_id)
    db.commit()
    return result
