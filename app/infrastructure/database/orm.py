from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, LargeBinary
from sqlalchemy.orm import relationship, declarative_base, deferred

Base = declarative_base()


class CompanySettings(Base):
    __tablename__ = "company_settings"
    id = Column(Integer, primary_key=True)
    registration_number = Column(String(20))
    company_name = Column(String(100))
    owner_name = Column(String(50))
    address = Column(String(200))
    business_type = Column(String(50))
    business_category = Column(String(50))
    phone = Column(String(20))
    mobile = Column(String(20))
    email = Column(String(100))
    bank_account = Column(String(100))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    address = Column(String(200))
    memo = Column(Text)
    receivable_memo = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Estimate(Base):
    __tablename__ = "estimates"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    contractor_name = Column(String(100))
    estimate_date = Column(DateTime, nullable=False, default=datetime.now)
    subtotal = Column(Float, default=0)
    vat_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    memo = Column(Text)
    status = Column(String(10), default="작성")
    created_at = Column(DateTime, default=datetime.now)
    items = relationship("EstimateItem", back_populates="estimate", cascade="all, delete-orphan")
    maintenance_orders = relationship("MaintenanceOrder", back_populates="estimate")


class EstimateItem(Base):
    __tablename__ = "estimate_items"
    id = Column(Integer, primary_key=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    item_number = Column(Integer)
    region = Column(String(50))
    model_name = Column(String(100))
    spec = Column(String(100))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0)
    amount = Column(Float, default=0)
    vat = Column(Float, default=0)
    estimate = relationship("Estimate", back_populates="items")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(50), unique=True)
    old_code = Column(String(50), index=True)
    category = Column(String(50))
    model = Column(String(200))
    stock_quantity = Column(Integer, default=0)
    min_stock_quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
    dealer_price = Column(Float, default=0)
    center_price = Column(Float, default=0)
    consumer_price = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, index=True)


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String(200))
    reference_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)


class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    sale_date = Column(DateTime, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    machine_category = Column(String(20))
    memo = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    model_name = Column(String(100))
    product_code = Column(String(50))
    chassis_number = Column(String(100), index=True)
    total_amount = Column(Float, default=0)
    loan_amount = Column(Float, default=0)
    self_pay_amount = Column(Float, default=0)
    loan_code = Column(String(50))
    memo = Column(Text)
    sale = relationship("Sale", back_populates="items")


class MaintenanceOrder(Base):
    __tablename__ = "maintenance_orders"
    id = Column(Integer, primary_key=True)
    estimate_id = Column(Integer, ForeignKey("estimates.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    machine_type = Column(String(100))
    machine_number = Column(String(100))
    symptom = Column(Text)
    description = Column(Text)
    total_amount = Column(Float, default=0)
    status = Column(String(10), default="작업중")
    received_date = Column(DateTime, nullable=False, default=datetime.now)
    completed_date = Column(DateTime, nullable=True)
    released_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    estimate = relationship("Estimate", back_populates="maintenance_orders")
    parts = relationship("MaintenancePart", back_populates="maintenance", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="maintenance", cascade="all, delete-orphan")
    photos = relationship("MaintenancePhoto", back_populates="maintenance", cascade="all, delete-orphan")


class MaintenancePart(Base):
    __tablename__ = "maintenance_parts"
    id = Column(Integer, primary_key=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    part_name = Column(String(100))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, default=0)
    amount = Column(Float, default=0)
    maintenance = relationship("MaintenanceOrder", back_populates="parts")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance_orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, nullable=False, default=datetime.now)
    memo = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    maintenance = relationship("MaintenanceOrder", back_populates="payments")


class MaintenancePhoto(Base):
    __tablename__ = "maintenance_photos"
    id = Column(Integer, primary_key=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance_orders.id"), nullable=False)
    content_type = Column(String(50), nullable=False)
    image_data = deferred(Column(LargeBinary, nullable=True))
    drive_file_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    maintenance = relationship("MaintenanceOrder", back_populates="photos")


class FieldTrip(Base):
    __tablename__ = "field_trips"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    purpose = Column(String(200))
    status = Column(String(20), default="예정")
    result = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    chassis_number = Column(String(100))
    machine_type = Column(String(100))
    model_name = Column(String(100))
    purchase_date = Column(DateTime)
    memo = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
