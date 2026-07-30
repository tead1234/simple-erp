from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.application.sale_service import SaleService, get_sale_service
from app.infrastructure.database.session import get_db

VALID_CATEGORIES = {"작업기", "트랙터"}

router = APIRouter(prefix="/api/sales", tags=["sales"])


class SaleItemIn(BaseModel):
    product_name: str
    model_name: Optional[str] = None
    product_code: Optional[str] = None
    chassis_number: Optional[str] = None
    total_amount: float = 0
    loan_amount: float = 0
    loan_code: Optional[str] = None
    memo: Optional[str] = None

    @field_validator("product_name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("품목명을 입력하세요")
        return v

    @field_validator("total_amount", "loan_amount")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("금액은 0 이상이어야 합니다")
        return v

    @model_validator(mode="after")
    def loan_not_exceed(self):
        if self.loan_amount > self.total_amount:
            raise ValueError("정부대출금액이 총금액을 초과할 수 없습니다")
        return self


class SaleIn(BaseModel):
    sale_date: str
    customer_id: Optional[int] = None
    customer_name: str
    memo: Optional[str] = None
    machine_category: Optional[str] = None
    items: List[SaleItemIn]

    @field_validator("sale_date")
    @classmethod
    def valid_date(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)")
        return v

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("품목을 하나 이상 입력하세요")
        return v


@router.get("")
def list_sales(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    svc: SaleService = Depends(get_sale_service),
):
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(400, f"유효하지 않은 카테고리: {category}")
    return svc.list(category, q)


@router.get("/{sale_id}")
def get_sale(sale_id: int, svc: SaleService = Depends(get_sale_service)):
    return svc.get(sale_id)


@router.post("", status_code=201)
def create_sale(data: SaleIn, svc: SaleService = Depends(get_sale_service), db: Session = Depends(get_db)):
    try:
        result = svc.create(
            sale_date=data.sale_date,
            customer_name=data.customer_name,
            customer_id=data.customer_id,
            memo=data.memo,
            machine_category=data.machine_category,
            items=[i.model_dump() for i in data.items],
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{sale_id}")
def update_sale(sale_id: int, data: SaleIn, svc: SaleService = Depends(get_sale_service), db: Session = Depends(get_db)):
    try:
        result = svc.update(
            sale_id=sale_id,
            sale_date=data.sale_date,
            customer_name=data.customer_name,
            customer_id=data.customer_id,
            memo=data.memo,
            machine_category=data.machine_category,
            items=[i.model_dump() for i in data.items],
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{sale_id}", status_code=204)
def delete_sale(sale_id: int, svc: SaleService = Depends(get_sale_service), db: Session = Depends(get_db)):
    svc.delete(sale_id)
    db.commit()
