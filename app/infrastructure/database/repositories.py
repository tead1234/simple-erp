from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Depends

from app.domain.customer.entity import Customer
from app.domain.customer.repository import ICustomerRepository
from app.domain.sale.entity import Sale, SaleItem
from app.domain.sale.repository import ISaleRepository
from app.domain.maintenance.entity import MaintenanceOrder, MaintenancePart, Payment
from app.domain.maintenance.repository import IMaintenanceRepository
from app.domain.product.entity import Product
from app.domain.product.repository import IProductRepository
from app.domain.settings.entity import CompanySettings
from app.domain.settings.repository import ISettingsRepository
from app.domain.fieldtrip.entity import FieldTrip
from app.domain.fieldtrip.repository import IFieldTripRepository
from app.domain.estimate.entity import Estimate, EstimateItem
from app.domain.estimate.repository import IEstimateRepository
from app.domain.equipment.entity import Equipment
from app.domain.equipment.repository import IEquipmentRepository
from app.infrastructure.database.session import get_db
from app.infrastructure.database.orm import (
    Customer as ORM_Customer,
    Sale as ORM_Sale,
    SaleItem as ORM_SaleItem,
    MaintenanceOrder as ORM_Maintenance,
    MaintenancePart as ORM_Part,
    Payment as ORM_Payment,
    Product as ORM_Product,
    StockMovement as ORM_StockMovement,
    CompanySettings as ORM_Settings,
    FieldTrip as ORM_FieldTrip,
    Estimate as ORM_Estimate,
    EstimateItem as ORM_EstimateItem,
    Equipment as ORM_Equipment,
)


# ── Mappers ───────────────────────────────────────────────────────────────────

def _m_customer(o: ORM_Customer) -> Customer:
    return Customer(id=o.id, name=o.name, phone=o.phone, address=o.address, memo=o.memo)

def _m_sale_item(o: ORM_SaleItem) -> SaleItem:
    return SaleItem(
        id=o.id, sale_id=o.sale_id, product_name=o.product_name,
        model_name=o.model_name, product_code=o.product_code,
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
    return Product(id=o.id, name=o.name, code=o.code, category=o.category,
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
        o = self.db.query(ORM_Customer).filter(ORM_Customer.name == name).first()
        return _m_customer(o) if o else None

    def search(self, q: str) -> List[Customer]:
        query = self.db.query(ORM_Customer)
        if q:
            query = query.filter(ORM_Customer.name.contains(q) | ORM_Customer.phone.contains(q))
        return [_m_customer(c) for c in query.order_by(ORM_Customer.name).all()]

    def save(self, customer: Customer) -> Customer:
        if customer.id:
            o = self.db.query(ORM_Customer).filter(ORM_Customer.id == customer.id).first()
            o.name, o.phone, o.address, o.memo = customer.name, customer.phone, customer.address, customer.memo
        else:
            o = ORM_Customer(name=customer.name, phone=customer.phone, address=customer.address, memo=customer.memo)
            self.db.add(o)
        self.db.flush()
        return _m_customer(o)

    def delete(self, id: int) -> None:
        o = self.db.query(ORM_Customer).filter(ORM_Customer.id == id).first()
        if o:
            self.db.delete(o)
            self.db.flush()


# ── Sale ──────────────────────────────────────────────────────────────────────

class SqlSaleRepository(ISaleRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[Sale]:
        o = self.db.query(ORM_Sale).filter(ORM_Sale.id == id).first()
        return _m_sale(o) if o else None

    def list(self, machine_category: Optional[str] = None) -> List[Sale]:
        query = self.db.query(ORM_Sale)
        if machine_category:
            query = query.filter(ORM_Sale.machine_category == machine_category)
        return [_m_sale(o) for o in query.order_by(ORM_Sale.sale_date.desc()).limit(100).all()]

    def save(self, sale: Sale) -> Sale:
        o = ORM_Sale(sale_date=sale.sale_date, customer_id=sale.customer_id,
                     machine_category=sale.machine_category, memo=sale.memo)
        self.db.add(o)
        self.db.flush()
        for item in sale.items:
            self.db.add(ORM_SaleItem(
                sale_id=o.id, product_name=item.product_name, model_name=item.model_name,
                product_code=item.product_code, total_amount=item.total_amount,
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

    def save(self, product: Product) -> Product:
        if product.id:
            o = self.db.query(ORM_Product).filter(ORM_Product.id == product.id).first()
            o.name = product.name
            o.code = product.code
            o.category = product.category
            o.model = product.model
            o.stock_quantity = product.stock_quantity
            o.min_stock_quantity = product.min_stock_quantity
            o.unit_price = product.unit_price
            o.dealer_price = product.dealer_price
            o.center_price = product.center_price
            o.consumer_price = product.consumer_price
        else:
            o = ORM_Product(name=product.name, code=product.code, category=product.category,
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

    def list(self, status: Optional[str] = None) -> List[MaintenanceOrder]:
        query = self.db.query(ORM_Maintenance)
        if status:
            query = query.filter(ORM_Maintenance.status == status)
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

        monthly_revenue = self.db.query(func.sum(ORM_SaleItem.total_amount)).join(
            ORM_Sale, ORM_Sale.id == ORM_SaleItem.sale_id
        ).filter(
            extract("year", ORM_Sale.sale_date) == now.year,
            extract("month", ORM_Sale.sale_date) == now.month,
        ).scalar() or 0

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
                    receivable_map[c.name] = receivable_map.get(c.name, 0) + r

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

        low_stock = self.db.query(ORM_Product).filter(ORM_Product.stock_quantity <= 1).all()

        return {
            "monthly_revenue": monthly_revenue,
            "active_maintenance": active_maintenance,
            "total_receivable": total_receivable,
            "upcoming_fieldtrips": upcoming_fieldtrips,
            "recent_maintenance": recent_maintenance,
            "top_receivables": sorted(
                [{"customer_name": k, "total_receivable": v} for k, v in receivable_map.items()],
                key=lambda x: x["total_receivable"], reverse=True
            )[:5],
            "low_stock_items": [{"id": p.id, "name": p.name, "stock_quantity": p.stock_quantity}
                                 for p in low_stock],
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


# ── Equipment ─────────────────────────────────────────────────────────────────

def _m_equipment(o: ORM_Equipment) -> Equipment:
    return Equipment(id=o.id, customer_id=o.customer_id, chassis_number=o.chassis_number,
                     machine_type=o.machine_type, model_name=o.model_name,
                     purchase_date=o.purchase_date, memo=o.memo)


class SqlEquipmentRepository(IEquipmentRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> Optional[Equipment]:
        o = self.db.query(ORM_Equipment).filter(ORM_Equipment.id == id).first()
        return _m_equipment(o) if o else None

    def list(self) -> List[Equipment]:
        return [_m_equipment(o) for o in self.db.query(ORM_Equipment).order_by(ORM_Equipment.id.desc()).all()]

    def find_by_chassis(self, chassis_number: str) -> List[Equipment]:
        return [_m_equipment(o) for o in
                self.db.query(ORM_Equipment).filter(ORM_Equipment.chassis_number.contains(chassis_number)).all()]

    def find_by_customer(self, customer_id: int) -> List[Equipment]:
        return [_m_equipment(o) for o in
                self.db.query(ORM_Equipment).filter(ORM_Equipment.customer_id == customer_id).all()]

    def save(self, eq: Equipment) -> Equipment:
        if eq.id:
            o = self.db.query(ORM_Equipment).filter(ORM_Equipment.id == eq.id).first()
            o.customer_id = eq.customer_id
            o.chassis_number = eq.chassis_number
            o.machine_type = eq.machine_type
            o.model_name = eq.model_name
            o.purchase_date = eq.purchase_date
            o.memo = eq.memo
        else:
            o = ORM_Equipment(customer_id=eq.customer_id, chassis_number=eq.chassis_number,
                              machine_type=eq.machine_type, model_name=eq.model_name,
                              purchase_date=eq.purchase_date, memo=eq.memo)
            self.db.add(o)
        self.db.flush()
        return _m_equipment(o)

    def delete(self, id: int) -> None:
        o = self.db.query(ORM_Equipment).filter(ORM_Equipment.id == id).first()
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

def get_equipment_repo(db: Session = Depends(get_db)) -> IEquipmentRepository:
    return SqlEquipmentRepository(db)

def get_fieldtrip_repo(db: Session = Depends(get_db)) -> IFieldTripRepository:
    return SqlFieldTripRepository(db)

def get_dashboard_query(db: Session = Depends(get_db)) -> DashboardQuery:
    return DashboardQuery(db)

def get_estimate_repo(db: Session = Depends(get_db)) -> IEstimateRepository:
    return SqlEstimateRepository(db)
