from fastapi import Depends, HTTPException, UploadFile
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

    def create(self, name: str, code: str = None, category: str = None, model: str = None,
               stock_quantity: int = 0, min_stock_quantity: int = 0, unit_price: float = 0,
               dealer_price: float = 0, center_price: float = 0, consumer_price: float = 0) -> dict:
        p = self.repo.save(Product(
            name=name, code=code, category=category, model=model,
            stock_quantity=stock_quantity, min_stock_quantity=min_stock_quantity,
            unit_price=unit_price, dealer_price=dealer_price,
            center_price=center_price, consumer_price=consumer_price,
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

    def import_from_excel(self, file_bytes: bytes) -> dict:
        import openpyxl, io
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb["복사 붙혀넣기"]

        created = 0
        updated = 0
        skipped = 0
        seen_codes = set()

        for row in ws.iter_rows(min_row=3, values_only=True):
            code = row[1]
            name = row[3]
            if not code or not name:
                continue
            code = str(code).strip()
            name = str(name).strip()
            if code in seen_codes:
                skipped += 1
                continue
            seen_codes.add(code)

            model = str(row[4]).strip() if row[4] else None
            unit_price = float(row[5]) if row[5] else 0.0
            dealer_price = float(row[6]) if row[6] else 0.0
            center_price = float(row[7]) if row[7] else 0.0
            consumer_price = float(row[8]) if row[8] else 0.0

            existing = self.repo.find_by_code(code)
            if existing:
                existing.name = name
                existing.model = model
                existing.unit_price = unit_price
                existing.dealer_price = dealer_price
                existing.center_price = center_price
                existing.consumer_price = consumer_price
                self.repo.save(existing)
                updated += 1
            else:
                self.repo.save(Product(
                    name=name, code=code, model=model,
                    unit_price=unit_price, dealer_price=dealer_price,
                    center_price=center_price, consumer_price=consumer_price,
                ))
                created += 1

        return {"created": created, "updated": updated, "skipped": skipped}

    def _to_dict(self, p: Product) -> dict:
        return {**p.__dict__, "is_low_stock": p.is_low_stock}


def get_inventory_service(repo: IProductRepository = Depends(get_product_repo)) -> InventoryService:
    return InventoryService(repo)
