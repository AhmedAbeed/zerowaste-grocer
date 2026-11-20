"""
app/schemas/api_schemas.py
Pydantic v2 schemas for ZeroWaste Grocer REST API Contract.
"""
from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# 1. Auth Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    role: str
    role_id: Optional[str] = None
    store_id: Optional[int] = None
    branch_id: Optional[int] = None

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
    on_hand_qty: int = Field(..., ge=0, description="Physical on-hand quantity cannot be negative")
    spoiled_qty: int = Field(..., ge=0, description="Spoiled quantity cannot be negative")

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

# 8. Phase 3: Incoming Batches (Clerk)
class IncomingBatchRequest(BaseModel):
    product_id: int
    batch_id: str
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")
    expiration_date: date

class IncomingBatchResponse(BaseModel):
    status: str = "success"
    batch_id: str
    product_id: int
    product_name: str
    store_id: int
    quantity: int
    expiration_date: str
    current_stock: int
    message: str

# 9. Phase 3: Admin Branch & Global Analytics
class BranchManagerInfo(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None

class BranchDetailResponse(BaseModel):
    id: int
    name: str
    location: str
    lat: float = 0.0
    lon: float = 0.0
    manager: Optional[BranchManagerInfo] = None
    product_count: int = 0
    active_stock: int = 0

class BranchCreateRequest(BaseModel):
    name: str
    location: str
    lat: float = 0.0
    lon: float = 0.0
    manager_id: Optional[int] = None

class StoreGlobalSummary(BaseModel):
    store_id: int
    store_name: str
    location: str
    product_count: int
    total_stock: int
    financial_loss: float

class GlobalAnalyticsResponse(BaseModel):
    total_stores: int
    total_products: int
    total_active_stock: int
    total_spoilage_units: int
    total_financial_loss: float
    total_diverted_kg: float
    stores: List[StoreGlobalSummary]

# 10. Phase 3: Broadcast System
class BroadcastCreateRequest(BaseModel):
    title: str
    message: str
    target_store_id: Optional[int] = None
    priority: str = "normal"

class BroadcastResponse(BaseModel):
    id: int
    title: str
    message: str
    target_store_id: Optional[int] = None
    target_store_name: Optional[str] = None
    created_at: str
    created_by: Optional[str] = None
    priority: str = "normal"

# 11. Phase 3: AI Ultra Endpoints
class UltraForecastRequest(BaseModel):
    product_id: int
    target_date: Optional[str] = None
    store_id: Optional[int] = None

class UltraForecastResponse(BaseModel):
    product_id: int
    product_name: str
    store_id: int
    target_date: str
    predicted_demand: float
    recommended_order_units: int
    confidence_interval: Dict[str, Any]
    top_drivers: List[Dict[str, Any]]

class UltraFeedbackRequest(BaseModel):
    product_id: int
    feedback_date: Optional[str] = None
    store_id: Optional[int] = None
    predicted_demand: Optional[float] = None
    actual_demand: Optional[float] = None
    spoiled_units: int = 0
    discrepancy: Optional[float] = None
    notes: Optional[str] = None

class UltraFeedbackResponse(BaseModel):
    status: str = "success"
    feedback_id: int
    message: str

