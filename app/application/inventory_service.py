from fastapi import Depends, HTTPException
from app.domain.product.entity import Product
from app.domain.product.repository import IProductRepository
from app.infrastructure.database.repositories import get_product_repo


class InventoryService:
    def __init__(self, repo: IProductRepository):
        self.repo = repo

    def list(self, category=None) -> list:
        products = self.repo.list()
        if category:
            products = [p for p in products if p.category == category]
        return [self._to_dict(p) for p in products]

    def get(self, product_id: int) -> dict:
        p = self.repo.get(product_id)
        if not p:
            raise HTTPException(404, "상품을 찾을 수 없습니다")
        return self._to_dict(p)

    def create(self, name: str, code: str = None, category: str = None,
               stock_quantity: int = 0, min_stock_quantity: int = 0, unit_price: float = 0) -> dict:
        p = self.repo.save(Product(
            name=name, code=code, category=category,
            stock_quantity=stock_quantity, min_stock_quantity=min_stock_quantity, unit_price=unit_price,
        ))
        return self._to_dict(p)

    def update(self, product_id: int, **kwargs) -> dict:
        p = self.repo.get(product_id)
        if not p:
            raise HTTPException(404, "상품을 찾을 수 없습니다")
        for k, v in kwargs.items():
            if v is not None and hasattr(p, k):
                setattr(p, k, v)
        p = self.repo.save(p)
        return self._to_dict(p)

    def adjust_stock(self, product_id: int, movement_type: str, quantity: int, reason: str = None) -> dict:
        p = self.repo.get(product_id)
        if not p:
            raise HTTPException(404, "상품을 찾을 수 없습니다")
        if movement_type == "출고" and p.stock_quantity < quantity:
            raise HTTPException(400, "재고가 부족합니다")
        self.repo.add_movement(product_id, movement_type, quantity, reason)
        if movement_type == "입고":
            p.stock_quantity += quantity
        else:
            p.stock_quantity -= quantity
        p = self.repo.save(p)
        return self._to_dict(p)

    def find_low_stock(self) -> list:
        return [self._to_dict(p) for p in self.repo.find_low_stock()]

    def _to_dict(self, p: Product) -> dict:
        return {**p.__dict__, "is_low_stock": p.is_low_stock}


def get_inventory_service(repo: IProductRepository = Depends(get_product_repo)) -> InventoryService:
    return InventoryService(repo)
