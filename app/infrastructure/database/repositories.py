from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Depends

from app.domain.customer.entity import Customer
from app.domain.customer.repository import ICustomerRepository
from app.domain.sale.entity import Sale, SaleItem
from app.domain.sale.repository import ISaleRepository
from app.domain.maintenance.entity import MaintenanceOrder, MaintenancePart, Payment, MaintenancePhoto
from app.domain.maintenance.repository import IMaintenanceRepository
from app.domain.product.entity import Product
from app.domain.product.repository import IProductRepository
from app.domain.settings.entity import CompanySettings
from app.domain.settings.repository import ISettingsRepository
from app.domain.fieldtrip.entity import FieldTrip
from app.domain.fieldtrip.repository import IFieldTripRepository
from app.domain.estimate.entity import Estimate, EstimateItem
from app.domain.estimate.repository import IEstimateRepository
from app.infrastructure.database.session import get_db
from app.infrastructure.storage import google_drive
from app.infrastructure.database.orm import (
    Customer as ORM_Customer,
    Sale as ORM_Sale,
    SaleItem as ORM_SaleItem,
    MaintenanceOrder as ORM_Maintenance,
    MaintenancePart as ORM_Part,
    Payment as ORM_Payment,
    MaintenancePhoto as ORM_Photo,
    Product as ORM_Product,
    StockMovement as ORM_StockMovement,
    CompanySettings as ORM_Settings,
    FieldTrip as ORM_FieldTrip,
    Estimate as ORM_Estimate,
    EstimateItem as ORM_EstimateItem,
)


# ── Mappers ───────────────────────────────────────────────────────────────────

def _m_customer(o: ORM_Customer) -> Customer:
    return Customer(id=o.id, name=o.name, phone=o.phone, address=o.address, memo=o.memo,
                     receivable_memo=o.receivable_memo, is_active=o.is_active)

def _m_sale_item(o: ORM_SaleItem) -> SaleItem:
    return SaleItem(
        id=o.id, sale_id=o.sale_id, product_name=o.product_name,
        model_name=o.model_name, product_code=o.product_code, chassis_number=o.chassis_number,
        total_amount=o.total_amount, loan_amount=o.loan_amount,
        self_pay_amount=o.self_pay_amount, loan_code=o.loan_code, memo=o.memo,
    )

def _m_sale(o: ORM_Sale) -> Sale:
    return Sale(
        id=o.id, sale_date=o.sale_date, customer_id=o.customer_id,
        memo=o.memo, machine_category=o.machine_category,
        items=[_m_sale_item(i) for i in o.items],
    )

def _m_maintenance(o: ORM_Maintenance) -> MaintenanceOrder:
    return MaintenanceOrder(
        id=o.id, customer_id=o.customer_id, estimate_id=o.estimate_id,
        received_date=o.received_date, machine_type=o.machine_type,
        machine_number=o.machine_number, symptom=o.symptom,
        description=o.description, total_amount=o.total_amount or 0,
        status=o.status, completed_date=o.completed_date, released_date=o.released_date,
        parts=[MaintenancePart(
            id=p.id, maintenance_id=p.maintenance_id, product_id=p.product_id,
            part_name=p.part_name, quantity=p.quantity, unit_price=p.unit_price, amount=p.amount,
        ) for p in o.parts],
        payments=[Payment(
            id=p.id, maintenance_id=p.maintenance_id,
            amount=p.amount, payment_date=p.payment_date, memo=p.memo,
        ) for p in o.payments],
        photos=[MaintenancePhoto(
            id=p.id, maintenance_id=p.maintenance_id,
            content_type=p.content_type, drive_file_id=p.drive_file_id, created_at=p.created_at,
        ) for p in o.photos],
    )

def _m_settings(o: ORM_Settings) -> CompanySettings:
    return CompanySettings(
        id=o.id, registration_number=o.registration_number,
        company_name=o.company_name, owner_name=o.owner_name,
        address=o.address, business_type=o.business_type,
        business_category=o.business_category, phone=o.phone,
        mobile=o.mobile, email=o.email, bank_account=o.bank_account,
    )

def _m_product(o: ORM_Product) -> Product:
    return Product(id=o.id, name=o.name, code=o.code, old_code=o.old_code, category=o.category,
                   model=o.model,
                   stock_quantity=o.stock_quantity, min_stock_quantity=o.min_stock_quantity,
                   unit_price=o.unit_price or 0,
                   dealer_price=o.dealer_price or 0,
                   center_price=o.center_price or 0,
                   consumer_price=o.consumer_price or 0)

def _m_fieldtrip(o: ORM_FieldTrip) -> FieldTrip:
    return FieldTrip(id=o.id, customer_id=o.customer_id,
                     scheduled_date=o.scheduled_date, purpose=o.purpose,
                     status=o.status, result=o.result)

def _m_estimate(o: ORM_Estimate) -> Estimate:
    return Estimate(
        id=o.id, customer_id=o.customer_id, contractor_name=o.contractor_name,
        estimate_date=o.estimate_date, subtotal=o.subtotal or 0,
        vat_amount=o.vat_amount or 0, total_amount=o.total_amount or 0,
        memo=o.memo, status=o.status,
        items=[EstimateItem(
            id=i.id, estimate_id=i.estimate_id, item_number=i.item_number, product_id=i.product_id,
            region=i.region, model_name=i.model_name, spec=i.spec,
            quantity=i.quantity, unit_price=i.unit_price, amount=i.amount, vat=i.vat,
        ) for i in o.items],
    )


# ── Customer ──────────────────────────────────────────────────────────────────

class SqlCustomerRepository(ICustomerRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[Customer]:
        o = self.db.query(ORM_Customer).filter(ORM_Customer.id == id).first()
        return _m_customer(o) if o else None

    def find_by_name(self, name: str) -> Optional[Customer]:
        o = self.db.query(ORM_Customer).filter(
            ORM_Customer.name == name, ORM_Customer.is_active == True  # noqa: E712
        ).first()
        return _m_customer(o) if o else None

    def search(self, q: str) -> List[Customer]:
        query = self.db.query(ORM_Customer).filter(ORM_Customer.is_active == True)  # noqa: E712
        if q:
            query = query.filter(ORM_Customer.name.contains(q) | ORM_Customer.phone.contains(q))
        return [_m_customer(c) for c in query.order_by(ORM_Customer.name).all()]

    def save(self, customer: Customer) -> Customer:
        if customer.id:
            o = self.db.query(ORM_Customer).filter(ORM_Customer.id == customer.id).first()
            o.name, o.phone, o.address, o.memo, o.receivable_memo = \
                customer.name, customer.phone, customer.address, customer.memo, customer.receivable_memo
        else:
            o = ORM_Customer(name=customer.name, phone=customer.phone, address=customer.address,
                              memo=customer.memo, receivable_memo=customer.receivable_memo)
            self.db.add(o)
        self.db.flush()
        return _m_customer(o)

    def delete(self, id: int) -> None:
        # 판매/정비/출장 이력이 customer_id를 참조하므로 실제로 지우지 않고 목록에서만 숨김(소프트 삭제)
        o = self.db.query(ORM_Customer).filter(ORM_Customer.id == id).first()
        if o:
            o.is_active = False
            self.db.flush()


# ── Sale ──────────────────────────────────────────────────────────────────────

class SqlSaleRepository(ISaleRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[Sale]:
        o = self.db.query(ORM_Sale).filter(ORM_Sale.id == id).first()
        return _m_sale(o) if o else None

    def list(self, machine_category: Optional[str] = None, q: Optional[str] = None) -> List[Sale]:
        query = self.db.query(ORM_Sale)
        if machine_category:
            query = query.filter(ORM_Sale.machine_category == machine_category)
        if q:
            query = query.join(ORM_SaleItem, ORM_SaleItem.sale_id == ORM_Sale.id) \
                         .filter(ORM_SaleItem.chassis_number.like(f"%{q}%")) \
                         .distinct()
        return [_m_sale(o) for o in query.order_by(ORM_Sale.sale_date.desc()).limit(100).all()]

    def save(self, sale: Sale) -> Sale:
        o = ORM_Sale(sale_date=sale.sale_date, customer_id=sale.customer_id,
                     machine_category=sale.machine_category, memo=sale.memo)
        self.db.add(o)
        self.db.flush()
        for item in sale.items:
            self.db.add(ORM_SaleItem(
                sale_id=o.id, product_name=item.product_name, model_name=item.model_name,
                product_code=item.product_code, chassis_number=item.chassis_number,
                total_amount=item.total_amount,
                loan_amount=item.loan_amount, self_pay_amount=item.self_pay_amount,
                loan_code=item.loan_code, memo=item.memo,
            ))
        return _m_sale(o)


# ── Product ───────────────────────────────────────────────────────────────────

class SqlProductRepository(IProductRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[Product]:
        o = self.db.query(ORM_Product).filter(ORM_Product.id == id).first()
        return _m_product(o) if o else None

    def list(self) -> List[Product]:
        return [_m_product(o) for o in self.db.query(ORM_Product).order_by(ORM_Product.name).all()]

    def find_low_stock(self) -> List[Product]:
        return [_m_product(o) for o in
                self.db.query(ORM_Product).filter(
                    ORM_Product.stock_quantity <= ORM_Product.min_stock_quantity
                ).all()]

    def find_by_code(self, code: str) -> Optional[Product]:
        o = self.db.query(ORM_Product).filter(ORM_Product.code == code).with_for_update().first()
        return _m_product(o) if o else None

    def recent(self, limit: int = 50) -> List[Product]:
        return [_m_product(o) for o in
                self.db.query(ORM_Product).order_by(ORM_Product.updated_at.desc()).limit(limit).all()]

    def search(self, q: str, limit: int = 30) -> List[Product]:
        like = f"%{q}%"
        return [_m_product(o) for o in
                self.db.query(ORM_Product).filter(
                    ORM_Product.code.like(like) |
                    ORM_Product.old_code.like(like) |
                    ORM_Product.name.like(like)
                ).order_by(ORM_Product.name).limit(limit).all()]

    def save(self, product: Product) -> Product:
        # 빈 문자열 품번은 NULL로 정규화 — SQLite UNIQUE는 빈 문자열끼리도 충돌시키지만 NULL끼리는 허용함
        code = (product.code or "").strip() or None
        if product.id:
            o = self.db.query(ORM_Product).filter(ORM_Product.id == product.id).first()
            o.name = product.name
            o.code = code
            o.old_code = product.old_code
            o.category = product.category
            o.model = product.model
            o.stock_quantity = product.stock_quantity
            o.min_stock_quantity = product.min_stock_quantity
            o.unit_price = product.unit_price
            o.dealer_price = product.dealer_price
            o.center_price = product.center_price
            o.consumer_price = product.consumer_price
        else:
            o = ORM_Product(name=product.name, code=code, old_code=product.old_code, category=product.category,
                            model=product.model,
                            stock_quantity=product.stock_quantity,
                            min_stock_quantity=product.min_stock_quantity,
                            unit_price=product.unit_price,
                            dealer_price=product.dealer_price,
                            center_price=product.center_price,
                            consumer_price=product.consumer_price)
            self.db.add(o)
        self.db.flush()
        return _m_product(o)

    def add_movement(self, product_id: int, movement_type: str, quantity: int, reason: str) -> None:
        self.db.add(ORM_StockMovement(product_id=product_id, movement_type=movement_type,
                                      quantity=quantity, reason=reason))


# ── Maintenance ───────────────────────────────────────────────────────────────

class SqlMaintenanceRepository(IMaintenanceRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[MaintenanceOrder]:
        o = self.db.query(ORM_Maintenance).filter(ORM_Maintenance.id == id).first()
        return _m_maintenance(o) if o else None

    def list(self, status: Optional[str] = None, q: Optional[str] = None) -> List[MaintenanceOrder]:
        query = self.db.query(ORM_Maintenance)
        if status:
            query = query.filter(ORM_Maintenance.status == status)
        if q:
            like = f"%{q}%"
            query = query.outerjoin(ORM_Customer, ORM_Maintenance.customer_id == ORM_Customer.id) \
                         .outerjoin(ORM_Part, ORM_Part.maintenance_id == ORM_Maintenance.id) \
                         .filter(ORM_Customer.name.like(like) | ORM_Part.part_name.like(like)) \
                         .distinct()
        return [_m_maintenance(o) for o in query.order_by(ORM_Maintenance.received_date.desc()).limit(200).all()]

    def save(self, order: MaintenanceOrder) -> MaintenanceOrder:
        if order.id:
            o = self.db.query(ORM_Maintenance).filter(ORM_Maintenance.id == order.id).with_for_update().first()
            o.status = order.status
            o.description = order.description
            o.total_amount = order.total_amount
            o.completed_date = order.completed_date
            o.released_date = order.released_date
        else:
            o = ORM_Maintenance(
                customer_id=order.customer_id, estimate_id=order.estimate_id,
                received_date=order.received_date, machine_type=order.machine_type,
                machine_number=order.machine_number, symptom=order.symptom, status=order.status,
            )
            self.db.add(o)
        self.db.flush()
        return _m_maintenance(o)

    def add_payment(self, maintenance_id: int, amount: float, payment_date, memo: Optional[str]) -> dict:
        o = self.db.query(ORM_Maintenance).filter(ORM_Maintenance.id == maintenance_id).with_for_update().first()
        p = ORM_Payment(maintenance_id=maintenance_id, amount=amount, payment_date=payment_date, memo=memo)
        self.db.add(p)
        self.db.flush()
        self.db.refresh(o)
        paid = sum(p.amount for p in o.payments)
        receivable = max(0.0, round((o.total_amount or 0) - paid, 2))
        return {
            "receivable": receivable,
            "paid_amount": round(paid, 2),
            "is_settled": receivable == 0,
        }

    def add_part(self, maintenance_id: int, part_name: str, quantity: int, unit_price: float,
                 product_id: Optional[int] = None) -> dict:
        amount = round(quantity * unit_price, 2)
        p = ORM_Part(maintenance_id=maintenance_id, part_name=part_name, product_id=product_id,
                     quantity=quantity, unit_price=unit_price, amount=amount)
        self.db.add(p)
        self.db.flush()
        return {"id": p.id, "part_name": p.part_name, "quantity": p.quantity,
                "unit_price": p.unit_price, "amount": p.amount, "product_id": p.product_id}

    def delete_part(self, part_id: int) -> None:
        p = self.db.query(ORM_Part).filter(ORM_Part.id == part_id).first()
        if p:
            self.db.delete(p)
            self.db.flush()

    def delete(self, id: int) -> None:
        o = self.db.query(ORM_Maintenance).filter(ORM_Maintenance.id == id).first()
        if not o:
            return
        for photo in o.photos:
            google_drive.delete(photo.drive_file_id)
        self.db.delete(o)
        self.db.flush()

    def find_by_estimate_id(self, estimate_id: int):
        o = self.db.query(ORM_Maintenance).filter(ORM_Maintenance.estimate_id == estimate_id).first()
        return _m_maintenance(o) if o else None

    def replace_parts(self, maintenance_id: int, parts: list) -> None:
        self.db.query(ORM_Part).filter(ORM_Part.maintenance_id == maintenance_id).delete()
        self.db.flush()
        for p in parts:
            amount = round(p["quantity"] * p["unit_price"], 2)
            self.db.add(ORM_Part(
                maintenance_id=maintenance_id,
                part_name=p["part_name"],
                product_id=p.get("product_id"),
                quantity=p["quantity"],
                unit_price=p["unit_price"],
                amount=amount,
            ))
        self.db.flush()

    def delete_payments(self, maintenance_id: int) -> None:
        self.db.query(ORM_Payment).filter(ORM_Payment.maintenance_id == maintenance_id).delete()
        self.db.flush()

    def add_photo(self, maintenance_id: int, content_type: str, image_data: bytes) -> dict:
        filename = f"maintenance_{maintenance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        drive_file_id = google_drive.upload(filename, content_type, image_data)
        p = ORM_Photo(maintenance_id=maintenance_id, content_type=content_type, drive_file_id=drive_file_id)
        self.db.add(p)
        self.db.flush()
        return {"id": p.id, "content_type": p.content_type, "created_at": p.created_at.isoformat()}

    def delete_photo(self, photo_id: int) -> None:
        p = self.db.query(ORM_Photo).filter(ORM_Photo.id == photo_id).first()
        if p:
            google_drive.delete(p.drive_file_id)
            self.db.delete(p)
            self.db.flush()

    def get_photo(self, photo_id: int) -> Optional[tuple]:
        p = self.db.query(ORM_Photo).filter(ORM_Photo.id == photo_id).first()
        if not p:
            return None
        try:
            return (p.content_type, google_drive.download(p.drive_file_id))
        except FileNotFoundError:
            return None


# ── Settings ──────────────────────────────────────────────────────────────────

class SqlSettingsRepository(ISettingsRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self) -> Optional[CompanySettings]:
        o = self.db.query(ORM_Settings).first()
        return _m_settings(o) if o else None

    def save(self, settings: CompanySettings) -> None:
        o = self.db.query(ORM_Settings).first()
        if not o:
            o = ORM_Settings()
            self.db.add(o)
        for k, v in settings.__dict__.items():
            if k != "id" and hasattr(o, k):
                setattr(o, k, v)
        o.updated_at = datetime.now()


# ── Dashboard query (CQRS read model) ────────────────────────────────────────

class DashboardQuery:
    def __init__(self, db: Session):
        self.db = db

    def stats(self) -> dict:
        from sqlalchemy import func, extract
        now = datetime.now()

        monthly_sales_revenue = self.db.query(func.sum(ORM_SaleItem.total_amount)).join(
            ORM_Sale, ORM_Sale.id == ORM_SaleItem.sale_id
        ).filter(
            extract("year", ORM_Sale.sale_date) == now.year,
            extract("month", ORM_Sale.sale_date) == now.month,
        ).scalar() or 0

        monthly_maintenance_revenue = self.db.query(func.sum(ORM_Maintenance.total_amount)).filter(
            ORM_Maintenance.status.in_(["완료", "출고"]),
            extract("year", ORM_Maintenance.completed_date) == now.year,
            extract("month", ORM_Maintenance.completed_date) == now.month,
        ).scalar() or 0

        monthly_revenue = monthly_sales_revenue + monthly_maintenance_revenue

        active_maintenance = self.db.query(func.count(ORM_Maintenance.id)).filter(
            ORM_Maintenance.status == "작업중"
        ).scalar() or 0

        upcoming_fieldtrips = self.db.query(func.count(ORM_FieldTrip.id)).filter(
            ORM_FieldTrip.status == "예정",
            ORM_FieldTrip.scheduled_date >= now,
        ).scalar() or 0

        all_orders = self.db.query(ORM_Maintenance).filter(ORM_Maintenance.total_amount > 0).all()
        customer_cache = {}

        def get_customer(cid):
            if cid not in customer_cache:
                customer_cache[cid] = self.db.query(ORM_Customer).filter(ORM_Customer.id == cid).first()
            return customer_cache[cid]

        total_receivable = 0
        receivable_map = {}
        for o in all_orders:
            paid = sum(p.amount for p in o.payments)
            r = max(0, (o.total_amount or 0) - paid)
            total_receivable += r
            if r > 0:
                c = get_customer(o.customer_id)
                if c:
                    entry = receivable_map.setdefault(c.id, {
                        "customer_id": c.id, "customer_name": c.name,
                        "total_receivable": 0, "memo": c.receivable_memo,
                    })
                    entry["total_receivable"] += r

        recent = self.db.query(ORM_Maintenance).order_by(ORM_Maintenance.received_date.desc()).limit(5).all()
        recent_maintenance = []
        for o in recent:
            c = get_customer(o.customer_id)
            paid = sum(p.amount for p in o.payments)
            recent_maintenance.append({
                "id": o.id,
                "customer_name": c.name if c else "-",
                "machine_type": o.machine_type,
                "status": o.status,
                "total_amount": o.total_amount,
                "receivable": max(0, (o.total_amount or 0) - paid),
            })

        # 엑셀 이관 재고에 수량 데이터가 없어 임시로 꺼둠. 재고수량 재입력 후 원복.
        low_stock = []

        return {
            "monthly_revenue": monthly_revenue,
            "active_maintenance": active_maintenance,
            "total_receivable": total_receivable,
            "upcoming_fieldtrips": upcoming_fieldtrips,
            "recent_maintenance": recent_maintenance,
            "top_receivables": sorted(
                receivable_map.values(),
                key=lambda x: x["total_receivable"], reverse=True
            )[:5],
            "low_stock_items": [{"id": p.id, "name": p.name, "stock_quantity": p.stock_quantity}
                                 for p in low_stock],
        }

    def revenue_detail(self, year: int, month: int) -> dict:
        from sqlalchemy import extract

        customer_cache = {}

        def get_customer_name(cid):
            if cid not in customer_cache:
                c = self.db.query(ORM_Customer).filter(ORM_Customer.id == cid).first()
                customer_cache[cid] = c.name if c else "-"
            return customer_cache[cid]

        sales = self.db.query(ORM_Sale).filter(
            extract("year", ORM_Sale.sale_date) == year,
            extract("month", ORM_Sale.sale_date) == month,
        ).all()

        items = []
        sales_total = 0
        for s in sales:
            total = sum(i.total_amount for i in s.items)
            sales_total += total
            summary = ", ".join(i.product_name for i in s.items if i.product_name)
            items.append({
                "date": s.sale_date.isoformat() if s.sale_date else None,
                "type": "판매",
                "customer_name": get_customer_name(s.customer_id),
                "description": summary,
                "amount": total,
                "source_id": s.id,
            })

        maintenance_orders = self.db.query(ORM_Maintenance).filter(
            ORM_Maintenance.status.in_(["완료", "출고"]),
            extract("year", ORM_Maintenance.completed_date) == year,
            extract("month", ORM_Maintenance.completed_date) == month,
        ).all()

        maintenance_total = 0
        for o in maintenance_orders:
            maintenance_total += o.total_amount or 0
            items.append({
                "date": o.completed_date.isoformat() if o.completed_date else None,
                "type": "정비",
                "customer_name": get_customer_name(o.customer_id),
                "description": o.machine_type,
                "amount": o.total_amount or 0,
                "source_id": o.id,
            })

        items.sort(key=lambda x: x["date"] or "", reverse=True)

        return {
            "year": year,
            "month": month,
            "sales_total": sales_total,
            "maintenance_total": maintenance_total,
            "total": sales_total + maintenance_total,
            "items": items,
        }


# ── FieldTrip ─────────────────────────────────────────────────────────────────

class SqlFieldTripRepository(IFieldTripRepository):
    def __init__(self, db: Session):
        self.db = db

    def list(self, status: Optional[str] = None) -> List[FieldTrip]:
        query = self.db.query(ORM_FieldTrip)
        if status:
            query = query.filter(ORM_FieldTrip.status == status)
        return [_m_fieldtrip(o) for o in query.order_by(ORM_FieldTrip.scheduled_date.desc()).all()]

    def get(self, id: int) -> Optional[FieldTrip]:
        o = self.db.query(ORM_FieldTrip).filter(ORM_FieldTrip.id == id).first()
        return _m_fieldtrip(o) if o else None

    def save(self, fieldtrip: FieldTrip) -> FieldTrip:
        if fieldtrip.id:
            o = self.db.query(ORM_FieldTrip).filter(ORM_FieldTrip.id == fieldtrip.id).first()
            o.status = fieldtrip.status
            o.result = fieldtrip.result
        else:
            o = ORM_FieldTrip(customer_id=fieldtrip.customer_id,
                              scheduled_date=fieldtrip.scheduled_date,
                              purpose=fieldtrip.purpose, status=fieldtrip.status)
            self.db.add(o)
        self.db.flush()
        return _m_fieldtrip(o)


# ── Estimate ──────────────────────────────────────────────────────────────────

class SqlEstimateRepository(IEstimateRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[Estimate]:
        o = self.db.query(ORM_Estimate).filter(ORM_Estimate.id == id).first()
        return _m_estimate(o) if o else None

    def list(self) -> List[Estimate]:
        return [_m_estimate(o) for o in
                self.db.query(ORM_Estimate).order_by(ORM_Estimate.estimate_date.desc()).all()]

    def save(self, estimate: Estimate) -> Estimate:
        if estimate.id:
            o = self.db.query(ORM_Estimate).filter(ORM_Estimate.id == estimate.id).first()
            o.status = estimate.status
            o.memo = estimate.memo
        else:
            o = ORM_Estimate(
                customer_id=estimate.customer_id,
                contractor_name=estimate.contractor_name,
                estimate_date=estimate.estimate_date,
                subtotal=estimate.subtotal,
                vat_amount=estimate.vat_amount,
                total_amount=estimate.total_amount,
                memo=estimate.memo,
                status=estimate.status,
            )
            self.db.add(o)
            self.db.flush()
            for idx, item in enumerate(estimate.items, 1):
                self.db.add(ORM_EstimateItem(
                    estimate_id=o.id, item_number=idx, product_id=item.product_id,
                    region=item.region, model_name=item.model_name,
                    spec=item.spec, quantity=item.quantity,
                    unit_price=item.unit_price, amount=item.amount, vat=item.vat,
                ))
        self.db.flush()
        self.db.refresh(o)
        return _m_estimate(o)

    def update(self, estimate: Estimate) -> Estimate:
        o = self.db.query(ORM_Estimate).filter(ORM_Estimate.id == estimate.id).first()
        o.contractor_name = estimate.contractor_name
        o.estimate_date = estimate.estimate_date
        o.subtotal = estimate.subtotal
        o.vat_amount = estimate.vat_amount
        o.total_amount = estimate.total_amount
        o.memo = estimate.memo
        for item in list(o.items):
            self.db.delete(item)
        self.db.flush()
        for idx, item in enumerate(estimate.items, 1):
            self.db.add(ORM_EstimateItem(
                estimate_id=o.id, item_number=idx, product_id=item.product_id,
                region=item.region, model_name=item.model_name,
                spec=item.spec, quantity=item.quantity,
                unit_price=item.unit_price, amount=item.amount, vat=item.vat,
            ))
        self.db.flush()
        self.db.refresh(o)
        return _m_estimate(o)

    def delete(self, id: int) -> None:
        o = self.db.query(ORM_Estimate).filter(ORM_Estimate.id == id).first()
        if o:
            self.db.delete(o)
            self.db.flush()


# ── FastAPI DI 팩토리 ─────────────────────────────────────────────────────────

def get_customer_repo(db: Session = Depends(get_db)) -> ICustomerRepository:
    return SqlCustomerRepository(db)

def get_sale_repo(db: Session = Depends(get_db)) -> ISaleRepository:
    return SqlSaleRepository(db)

def get_product_repo(db: Session = Depends(get_db)) -> IProductRepository:
    return SqlProductRepository(db)

def get_maintenance_repo(db: Session = Depends(get_db)) -> IMaintenanceRepository:
    return SqlMaintenanceRepository(db)

def get_settings_repo(db: Session = Depends(get_db)) -> ISettingsRepository:
    return SqlSettingsRepository(db)

def get_fieldtrip_repo(db: Session = Depends(get_db)) -> IFieldTripRepository:
    return SqlFieldTripRepository(db)

def get_dashboard_query(db: Session = Depends(get_db)) -> DashboardQuery:
    return DashboardQuery(db)

def get_estimate_repo(db: Session = Depends(get_db)) -> IEstimateRepository:
    return SqlEstimateRepository(db)
