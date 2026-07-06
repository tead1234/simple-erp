import io
from datetime import datetime
from typing import Optional, List
from fastapi import Depends, HTTPException
from PIL import Image
from app.domain.maintenance.entity import MaintenanceOrder, VALID_STATUSES
from app.domain.maintenance.repository import IMaintenanceRepository
from app.domain.customer.repository import ICustomerRepository
from app.domain.estimate.repository import IEstimateRepository
from app.domain.product.repository import IProductRepository
from app.infrastructure.database.repositories import (
    get_maintenance_repo, get_customer_repo, get_estimate_repo, get_product_repo,
)
from app.application.customer_service import CustomerService


MAX_PHOTOS_PER_ORDER = 4
MAX_PHOTO_DIMENSION = 1600
JPEG_QUALITY = 85


class MaintenanceService:
    def __init__(self, repo: IMaintenanceRepository, customer_repo: ICustomerRepository,
                 estimate_repo: IEstimateRepository, product_repo: IProductRepository):
        self._repo = repo
        self._customer_svc = CustomerService(customer_repo)
        self._estimate_repo = estimate_repo
        self._product_repo = product_repo

    def list(self, status: Optional[str] = None, q: Optional[str] = None) -> list:
        if status and status not in VALID_STATUSES:
            raise HTTPException(400, f"유효하지 않은 상태값: {status}")
        orders = self._repo.list(status, q)
        cache = {}

        def get_name(cid):
            if cid not in cache:
                c = self._customer_svc._repo.get(cid)
                cache[cid] = c.name if c else "-"
            return cache[cid]

        return [
            {
                "id": o.id,
                "received_date": o.received_date.isoformat() if o.received_date else None,
                "customer_name": get_name(o.customer_id),
                "machine_type": o.machine_type,
                "machine_number": o.machine_number,
                "status": o.status,
                "total_amount": o.total_amount,
                "receivable": o.receivable(),
            }
            for o in orders
        ]

    def get(self, order_id: int) -> dict:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")
        customer = self._customer_svc._repo.get(order.customer_id)
        paid = sum(p.amount for p in order.payments)
        return {
            "id": order.id,
            "estimate_id": order.estimate_id,
            "customer_name": customer.name if customer else "-",
            "customer_phone": customer.phone if customer else None,
            "machine_type": order.machine_type,
            "machine_number": order.machine_number,
            "symptom": order.symptom,
            "description": order.description,
            "status": order.status,
            "total_amount": order.total_amount,
            "paid_amount": round(paid, 2),
            "receivable": order.receivable(),
            "received_date": order.received_date.isoformat() if order.received_date else None,
            "completed_date": order.completed_date.isoformat() if order.completed_date else None,
            "released_date": order.released_date.isoformat() if order.released_date else None,
            "parts": [
                {"id": p.id, "part_name": p.part_name, "product_id": p.product_id,
                 "quantity": p.quantity, "unit_price": p.unit_price, "amount": p.amount}
                for p in order.parts
            ],
            "payments": [
                {"id": p.id, "amount": p.amount,
                 "payment_date": p.payment_date.isoformat(), "memo": p.memo}
                for p in order.payments
            ],
            "photos": [
                {"id": p.id, "created_at": p.created_at.isoformat() if p.created_at else None}
                for p in order.photos
            ],
        }

    def create(self, received_date: str, customer_name: str, customer_id: Optional[int],
               machine_type: Optional[str], machine_number: Optional[str],
               symptom: Optional[str], estimate_id: Optional[int]) -> dict:
        cid = self._customer_svc.get_or_create(customer_name, customer_id)
        order = self._repo.save(MaintenanceOrder(
            customer_id=cid,
            estimate_id=estimate_id,
            received_date=datetime.fromisoformat(received_date),
            machine_type=machine_type,
            machine_number=machine_number,
            symptom=symptom,
        ))
        if estimate_id:
            estimate = self._estimate_repo.get(estimate_id)
            if estimate:
                parts = [
                    {"part_name": i.model_name, "quantity": i.quantity,
                     "unit_price": i.unit_price_with_vat, "product_id": i.product_id}
                    for i in estimate.items
                ]
                self._repo.replace_parts(order.id, parts)
                order.total_amount = estimate.total_amount
                self._repo.save(order)
        return {"id": order.id}

    def update(self, order_id: int, status: Optional[str], description: Optional[str],
               total_amount: Optional[float]) -> dict:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")

        if status is not None and status != order.status:
            try:
                order.transition(status)
            except ValueError as e:
                raise HTTPException(400, str(e))
            if status == "출고":
                self._deduct_stock_for_parts(order)

        if description is not None:
            if order.status in ("완료", "출고"):
                raise HTTPException(400, "완료·출고된 정비는 작업내용을 수정할 수 없습니다")
            order.description = description

        if total_amount is not None:
            if order.status in ("완료", "출고"):
                raise HTTPException(400, "완료·출고된 정비는 수리금액을 수정할 수 없습니다")
            if order.estimate_id:
                raise HTTPException(400, "견적서와 연결된 정비의 수리금액은 견적서에서 자동으로 반영됩니다")
            order.total_amount = total_amount

        self._repo.save(order)
        return {"id": order.id}

    def add_part(self, order_id: int, product_id: int, quantity: int, unit_price: float) -> dict:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")
        if order.estimate_id:
            raise HTTPException(400, "견적서와 연결된 정비의 수리물품은 견적서에서 수정하세요")
        product = self._product_repo.get(product_id)
        if not product:
            raise HTTPException(400, "재고상품을 찾을 수 없습니다")
        if quantity <= 0:
            raise HTTPException(400, "수량은 1 이상이어야 합니다")
        if unit_price < 0:
            raise HTTPException(400, "단가는 0 이상이어야 합니다")
        return self._repo.add_part(order_id, product.name, quantity, unit_price, product_id=product.id)

    def delete_part(self, order_id: int, part_id: int) -> None:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")
        if order.estimate_id:
            raise HTTPException(400, "견적서와 연결된 정비의 수리물품은 견적서에서 수정하세요")
        self._repo.delete_part(part_id)

    def add_payment(self, order_id: int, amount: float, payment_date: str, memo: Optional[str]) -> dict:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")
        if not order.total_amount:
            raise HTTPException(400, "수리금액이 설정되지 않아 입금을 등록할 수 없습니다")
        receivable = order.receivable()
        if amount > receivable + 0.01:
            raise HTTPException(400, f"입금액({amount:,.0f}원)이 미수금({receivable:,.0f}원)을 초과합니다")
        return self._repo.add_payment(order_id, amount, datetime.fromisoformat(payment_date), memo)

    def cancel(self, order_id: int, confirmed_refund: bool = False) -> dict:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")

        paid = round(sum(p.amount for p in order.payments), 2)
        if paid > 0 and not confirmed_refund:
            raise HTTPException(
                409,
                f"이미 {paid:,.0f}원의 입금 내역이 있습니다. 환불 처리를 완료한 뒤 다시 취소해주세요.",
            )

        try:
            order.cancel()
        except ValueError as e:
            raise HTTPException(400, str(e))

        if paid > 0:
            self._repo.delete_payments(order_id)

        if order.released_date:
            self._restore_stock_for_parts(order)

        if order.estimate_id:
            estimate = self._estimate_repo.get(order.estimate_id)
            if estimate and estimate.status != "취소":
                estimate.cancel()
                self._estimate_repo.save(estimate)

        self._repo.save(order)
        return {"id": order.id, "status": order.status}

    def delete_order(self, order_id: int, confirmed_refund: bool = False) -> None:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")

        paid = round(sum(p.amount for p in order.payments), 2)
        if paid > 0 and not confirmed_refund:
            raise HTTPException(
                409,
                f"이미 {paid:,.0f}원의 입금 내역이 있습니다. 환불 처리를 완료한 뒤 다시 삭제해주세요.",
            )

        if order.released_date:
            self._restore_stock_for_parts(order)

        estimate_id = order.estimate_id
        self._repo.delete(order_id)
        if estimate_id:
            self._estimate_repo.delete(estimate_id)

    def add_photo(self, order_id: int, content_type: str, raw_bytes: bytes) -> dict:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")
        if order.status in ("완료", "출고"):
            raise HTTPException(400, "완료·출고된 정비는 사진을 추가할 수 없습니다")
        if len(order.photos) >= MAX_PHOTOS_PER_ORDER:
            raise HTTPException(400, f"사진은 최대 {MAX_PHOTOS_PER_ORDER}장까지 첨부할 수 있습니다")
        try:
            image = Image.open(io.BytesIO(raw_bytes))
            image = image.convert("RGB")
        except Exception:
            raise HTTPException(400, "올바른 이미지 파일이 아닙니다")
        image.thumbnail((MAX_PHOTO_DIMENSION, MAX_PHOTO_DIMENSION))
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=JPEG_QUALITY)
        return self._repo.add_photo(order_id, "image/jpeg", buf.getvalue())

    def delete_photo(self, order_id: int, photo_id: int) -> None:
        order = self._repo.get(order_id)
        if not order:
            raise HTTPException(404, "정비 내역을 찾을 수 없습니다")
        if order.status in ("완료", "출고"):
            raise HTTPException(400, "완료·출고된 정비는 사진을 삭제할 수 없습니다")
        self._repo.delete_photo(photo_id)

    def get_photo(self, photo_id: int) -> tuple:
        result = self._repo.get_photo(photo_id)
        if not result:
            raise HTTPException(404, "사진을 찾을 수 없습니다")
        return result

    def _stock_quantities(self, order: MaintenanceOrder) -> dict:
        needed: dict = {}
        for part in order.parts:
            if part.product_id:
                needed[part.product_id] = needed.get(part.product_id, 0) + part.quantity
        return needed

    def _deduct_stock_for_parts(self, order: MaintenanceOrder) -> None:
        needed = self._stock_quantities(order)
        for pid, qty in needed.items():
            product = self._product_repo.get(pid)
            if not product:
                continue
            product.stock_quantity -= qty
            self._product_repo.save(product)
            self._product_repo.add_movement(pid, "출고", qty, f"정비 #{order.id} 출고")

    def _restore_stock_for_parts(self, order: MaintenanceOrder) -> None:
        needed = self._stock_quantities(order)
        for pid, qty in needed.items():
            product = self._product_repo.get(pid)
            if not product:
                continue
            product.stock_quantity += qty
            self._product_repo.save(product)
            self._product_repo.add_movement(pid, "입고", qty, f"정비 #{order.id} 취소 재고복구")


def get_maintenance_service(
    repo: IMaintenanceRepository = Depends(get_maintenance_repo),
    customer_repo: ICustomerRepository = Depends(get_customer_repo),
    estimate_repo: IEstimateRepository = Depends(get_estimate_repo),
    product_repo: IProductRepository = Depends(get_product_repo),
) -> MaintenanceService:
    return MaintenanceService(repo, customer_repo, estimate_repo, product_repo)
