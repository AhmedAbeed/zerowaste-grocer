"""
app/schemas/api_schemas.py
Pydantic v2 schemas for ZeroWaste Grocer REST API Contract.
"""
from typing import Optional, List
from pydantic import BaseModel, Field

# 1. Auth Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    role: str
    store_id: Optional[int] = None

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

# 2. Store Schemas
class StoreCreateRequest(BaseModel):
    name: str
    location: str
    lat: float = 0.0
    lon: float = 0.0

class StoreResponse(BaseModel):
    id: int
    name: str
    location: str

# 3. Inventory & Batches Schemas
class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    unit_cost: float
    unit_price: float
    shelf_life_days: int
    safety_stock: int
    current_stock: int

class InventoryResponse(BaseModel):
    store_id: int
    store_name: str
    items: List[ProductResponse]

class BatchResponse(BaseModel):
    id: str
    product_id: int
    received_date: str
    expiration_date: str
    remaining_qty: int
    discount_pct: float
    days_to_expiry: Optional[int] = None

class AuditEntrySchema(BaseModel):
    product_id: int
    on_hand_qty: int
    spoiled_qty: int

class AuditSubmitRequest(BaseModel):
    store_id: int
    entries: List[AuditEntrySchema]

class AuditSubmitResponse(BaseModel):
    status: str = "success"
    updated_count: int
    message: str

# 4. Replenishment Schemas
class XaiDriverSchema(BaseModel):
    label: str
    impact_pct: float

class RecommendationItemSchema(BaseModel):
    product_id: int
    product_name: str
    category: str
    current_stock: int
    safety_stock: int
    predicted_demand: int
    recommended_qty: int
    approved_qty: int
    status: str = "pending"
    xai_reason: str
    xai_drivers: List[XaiDriverSchema]
    sigma_e: Optional[float] = None
    sigma_source: Optional[str] = None
    approved: bool = False

class RecommendationsResponse(BaseModel):
    store_id: int
    target_date: str
    total_items: int
    items: List[RecommendationItemSchema]

class ApprovalItemSchema(BaseModel):
    product_id: int
    final_qty: int
    override_reason: Optional[str] = None

class ApprovalRequest(BaseModel):
    store_id: int
    items: List[ApprovalItemSchema]

class ApprovalResponse(BaseModel):
    status: str = "success"
    order_id: int
    approved_items_count: int
    total_units: int

# 5. Alerts & Markdowns Schemas
class AlertResponse(BaseModel):
    id: str
    batch_id: Optional[str] = None
    product_id: int
    product_name: str
    days_to_expiry: int
    remaining_qty: int
    predicted_demand: int
    suggested_discount_pct: float
    status: str = "open"
    applied_discount_pct: Optional[float] = None

class AlertsListResponse(BaseModel):
    store_id: int
    active_alerts_count: int
    units_at_risk: int
    items: List[AlertResponse]

class MarkdownActionRequest(BaseModel):
    alert_id: str
    action: str  # "accept" | "dismiss"

class MarkdownActionResponse(BaseModel):
    status: str = "success"
    alert_id: str
    current_discount_pct: float
    message: str

# 6. Analytics & Dashboard Schemas
class WasteMetricsResponse(BaseModel):
    units_at_risk: int
    projected_exposure: float
    pending_orders: int
    kg_saved: float
    co2_saved: float

class SalesPointResponse(BaseModel):
    date: str
    actual: float
    predicted: float

class CategoryWasteResponse(BaseModel):
    category: str
    units: int

# 7. Level 3 Notification & Dismiss Schemas
class NotificationSchema(BaseModel):
    id: int
    store_id: int
    type: str
    title: str
    body: str
    batch_id: Optional[str] = None
    created_at: str
    is_read: bool

class NotificationListResponse(BaseModel):
    items: List[NotificationSchema]
    unread_count: int

class NotificationReadResponse(BaseModel):
    id: int
    is_read: bool

class DismissAlertResponse(BaseModel):
    batch_id: str
    dismissed_until: str
    status: str

class RunJobResponse(BaseModel):
    stores_processed: int
    alerts_found: int
    notifications_created: int
    skipped_duplicates: int
    skipped_dismissed: int
