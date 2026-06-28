from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.application.inventory_service import InventoryService, get_inventory_service
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class ProductIn(BaseModel):
    name: str
    code: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: int = 0
    min_stock_quantity: int = 0
    unit_price: float = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    min_stock_quantity: Optional[int] = None
    unit_price: Optional[float] = None


class StockMovementIn(BaseModel):
    movement_type: str  # 입고 / 출고
    quantity: int
    reason: Optional[str] = None


@router.get("")
def list_products(category: Optional[str] = Query(None), svc: InventoryService = Depends(get_inventory_service)):
    return svc.list(category)


@router.get("/low-stock")
def low_stock(svc: InventoryService = Depends(get_inventory_service)):
    return svc.find_low_stock()


@router.get("/{product_id}")
def get_product(product_id: int, svc: InventoryService = Depends(get_inventory_service)):
    return svc.get(product_id)


@router.post("", status_code=201)
def create_product(data: ProductIn, svc: InventoryService = Depends(get_inventory_service), db: Session = Depends(get_db)):
    result = svc.create(**data.model_dump())
    db.commit()
    return result


@router.patch("/{product_id}")
def update_product(product_id: int, data: ProductUpdate, svc: InventoryService = Depends(get_inventory_service), db: Session = Depends(get_db)):
    result = svc.update(product_id, **data.model_dump(exclude_none=True))
    db.commit()
    return result


@router.post("/{product_id}/movements", status_code=201)
def stock_movement(product_id: int, data: StockMovementIn, svc: InventoryService = Depends(get_inventory_service), db: Session = Depends(get_db)):
    result = svc.adjust_stock(product_id, data.movement_type, data.quantity, data.reason)
    db.commit()
    return result
