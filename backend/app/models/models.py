"""
app/models/models.py
SQLAlchemy ORM models matching ZeroWaste Grocer relational schema.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import relationship, deferred
from app.db.base import Base

class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    daily_exogenous = relationship("DailyExogenous", back_populates="store", cascade="all, delete-orphan")
    replenishment_orders = relationship("ReplenishmentOrder", back_populates="store", cascade="all, delete-orphan")
    waste_logs = relationship("WasteLog", back_populates="store", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Store(id={self.id}, name='{self.name}')>"

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    shelf_life_days = Column(Integer, nullable=False)

    products = relationship("Product", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sku = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    unit_cost = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    safety_stock = Column(Integer, default=5, nullable=False)
    is_perishable = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("store_id", "sku", name="uq_store_product_sku"),
    )

    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")
    batches = relationship("ProductBatch", back_populates="product", cascade="all, delete-orphan")
    inventory_snapshots = relationship("InventorySnapshot", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    waste_logs = relationship("WasteLog", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', store_id={self.store_id})>"

class ProductBatch(Base):
    __tablename__ = "product_batches"

    id = Column(String(50), primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    received_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    initial_quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)
    current_discount_pct = Column(Float, default=0.0, nullable=False)

    product = relationship("Product", back_populates="batches")

    def __repr__(self):
        return f"<ProductBatch(id='{self.id}', product_id={self.product_id}, remaining={self.remaining_quantity})>"

class DailyExogenous(Base):
    __tablename__ = "daily_exogenous"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    record_date = Column(Date, nullable=False)
    avg_temp = Column(Float, nullable=True)
    avg_humidity = Column(Float, nullable=True)
    total_rain = Column(Float, nullable=True)
    foot_traffic_load = Column(Float, nullable=True)
    is_holiday = Column(Boolean, default=False, nullable=False)

    # Level 8: Individual calendar / holiday indicators
    is_before_holiday = deferred(Column(Float, nullable=True))
    is_after_holiday = deferred(Column(Float, nullable=True))
    is_school_holiday = deferred(Column(Float, nullable=True))
    is_weekend = deferred(Column(Float, nullable=True))
    is_weekday = deferred(Column(Float, nullable=True))
    day_of_year = deferred(Column(Float, nullable=True))
    month_val = deferred(Column(Float, nullable=True))
    is_lockdown = deferred(Column(Float, nullable=True))

    # Level 8: ERA5 hourly weather (32 columns)
    t2m_09 = deferred(Column(Float, nullable=True))
    t2m_12 = deferred(Column(Float, nullable=True))
    t2m_15 = deferred(Column(Float, nullable=True))
    t2m_18 = deferred(Column(Float, nullable=True))
    td2m_09 = deferred(Column(Float, nullable=True))
    td2m_12 = deferred(Column(Float, nullable=True))
    td2m_15 = deferred(Column(Float, nullable=True))
    td2m_18 = deferred(Column(Float, nullable=True))
    rh2m_09 = deferred(Column(Float, nullable=True))
    rh2m_12 = deferred(Column(Float, nullable=True))
    rh2m_15 = deferred(Column(Float, nullable=True))
    rh2m_18 = deferred(Column(Float, nullable=True))
    p0_09 = deferred(Column(Float, nullable=True))
    p0_12 = deferred(Column(Float, nullable=True))
    p0_15 = deferred(Column(Float, nullable=True))
    p0_18 = deferred(Column(Float, nullable=True))
    gl_09 = deferred(Column(Float, nullable=True))
    gl_12 = deferred(Column(Float, nullable=True))
    gl_15 = deferred(Column(Float, nullable=True))
    gl_18 = deferred(Column(Float, nullable=True))
    uu_09 = deferred(Column(Float, nullable=True))
    uu_12 = deferred(Column(Float, nullable=True))
    uu_15 = deferred(Column(Float, nullable=True))
    uu_18 = deferred(Column(Float, nullable=True))
    vv_09 = deferred(Column(Float, nullable=True))
    vv_12 = deferred(Column(Float, nullable=True))
    vv_15 = deferred(Column(Float, nullable=True))
    vv_18 = deferred(Column(Float, nullable=True))
    rr_09 = deferred(Column(Float, nullable=True))
    rr_12 = deferred(Column(Float, nullable=True))
    rr_15 = deferred(Column(Float, nullable=True))
    rr_18 = deferred(Column(Float, nullable=True))

    # Level 8: Foot traffic detail (3 columns)
    residents = deferred(Column(Float, nullable=True))
    visits = deferred(Column(Float, nullable=True))
    visitors = deferred(Column(Float, nullable=True))

    # Level 8: Hourly pedestrian load (24 columns)
    load_00 = deferred(Column(Float, nullable=True))
    load_01 = deferred(Column(Float, nullable=True))
    load_02 = deferred(Column(Float, nullable=True))
    load_03 = deferred(Column(Float, nullable=True))
    load_04 = deferred(Column(Float, nullable=True))
    load_05 = deferred(Column(Float, nullable=True))
    load_06 = deferred(Column(Float, nullable=True))
    load_07 = deferred(Column(Float, nullable=True))
    load_08 = deferred(Column(Float, nullable=True))
    load_09 = deferred(Column(Float, nullable=True))
    load_10 = deferred(Column(Float, nullable=True))
    load_11 = deferred(Column(Float, nullable=True))
    load_12 = deferred(Column(Float, nullable=True))
    load_13 = deferred(Column(Float, nullable=True))
    load_14 = deferred(Column(Float, nullable=True))
    load_15 = deferred(Column(Float, nullable=True))
    load_16 = deferred(Column(Float, nullable=True))
    load_17 = deferred(Column(Float, nullable=True))
    load_18 = deferred(Column(Float, nullable=True))
    load_19 = deferred(Column(Float, nullable=True))
    load_20 = deferred(Column(Float, nullable=True))
    load_21 = deferred(Column(Float, nullable=True))
    load_22 = deferred(Column(Float, nullable=True))
    load_23 = deferred(Column(Float, nullable=True))

    __table_args__ = (
        UniqueConstraint("store_id", "record_date", name="uq_store_record_date"),
    )

    store = relationship("Store", back_populates="daily_exogenous")

    def __repr__(self):
        return f"<DailyExogenous(store_id={self.store_id}, date={self.record_date})>"

class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    opening_stock = Column(Integer, nullable=False)
    units_sold = Column(Integer, default=0, nullable=False)
    units_spoiled = Column(Integer, default=0, nullable=False)
    closing_stock = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "snapshot_date", name="uq_product_snapshot_date"),
    )

    product = relationship("Product", back_populates="inventory_snapshots")

    def __repr__(self):
        return f"<InventorySnapshot(product_id={self.product_id}, date={self.snapshot_date}, sold={self.units_sold})>"

class ReplenishmentOrder(Base):
    __tablename__ = "replenishment_orders"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    order_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING, APPROVED, DISPATCHED, COMPLETED, CANCELLED
    total_amount = Column(Float, default=0.0, nullable=False)

    store = relationship("Store", back_populates="replenishment_orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ReplenishmentOrder(id={self.id}, store_id={self.store_id}, status='{self.status}')>"

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    order_id = Column(Integer, ForeignKey("replenishment_orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    predicted_demand = Column(Float, nullable=False)
    recommended_qty = Column(Integer, nullable=False)
    final_approved_qty = Column(Integer, nullable=False)
    xai_reason = Column(Text, nullable=True)

    order = relationship("ReplenishmentOrder", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"

class WasteLog(Base):
    __tablename__ = "waste_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    spoiled_quantity = Column(Integer, nullable=False)
    financial_loss = Column(Float, nullable=False)
    recorded_by = Column(String(100), nullable=True)

    product = relationship("Product", back_populates="waste_logs")
    store = relationship("Store", back_populates="waste_logs")

    def __repr__(self):
        return f"<WasteLog(id={self.id}, product_id={self.product_id}, loss=${self.financial_loss:.2f})>"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # storeManager, inventoryAuditor, systemAdmin
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    store = relationship("Store")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)   # e.g., "SPOILAGE_MARKDOWN"
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    batch_id = Column(String(50), ForeignKey("product_batches.id", ondelete="CASCADE"), nullable=True)
    alert_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("store_id", "batch_id", "type", "alert_date", name="uq_notification_daily"),
    )

    store = relationship("Store")
    batch = relationship("ProductBatch")

    def __repr__(self):
        return f"<Notification(id={self.id}, store_id={self.store_id}, type='{self.type}', is_read={self.is_read})>"


class AlertAction(Base):
    __tablename__ = "alert_actions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(String(50), ForeignKey("product_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(20), nullable=False)  # e.g., "DISMISSED"
    dismissed_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    store = relationship("Store")
    batch = relationship("ProductBatch")
    user = relationship("User")

    def __repr__(self):
        return f"<AlertAction(id={self.id}, batch_id='{self.batch_id}', action='{self.action}', until={self.dismissed_until})>"
