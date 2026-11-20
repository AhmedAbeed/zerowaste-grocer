"""
app/api/v1/endpoints/admin.py
System Admin management endpoints: branch oversight, global analytics, and broadcast dispatch.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.models import Store, Product, ProductBatch, WasteLog, User, Broadcast
from app.schemas.api_schemas import (
    BranchDetailResponse,
    BranchManagerInfo,
    BranchCreateRequest,
    GlobalAnalyticsResponse,
    StoreGlobalSummary,
    BroadcastCreateRequest,
    BroadcastResponse
)
from app.core.security import require_roles, normalize_role

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get(
    "/branches",
    response_model=List[BranchDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="List all branches with assigned manager and inventory summary (admin only)"
)
def get_admin_branches(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    stores = db.query(Store).order_by(Store.id.asc()).all()
    results = []

    for store in stores:
        mgr = db.query(User).filter(User.store_id == store.id, User.role == "manager").first()
        mgr_info = None
        if mgr:
            mgr_info = BranchManagerInfo(
                id=mgr.id,
                username=mgr.username,
                full_name=mgr.full_name,
                email=mgr.email
            )

        prod_count = db.query(func.count(Product.id)).filter(Product.store_id == store.id).scalar() or 0
        stock_sum = (
            db.query(func.sum(ProductBatch.remaining_quantity))
            .join(Product, Product.id == ProductBatch.product_id)
            .filter(Product.store_id == store.id, ProductBatch.remaining_quantity > 0)
            .scalar() or 0
        )

        results.append(BranchDetailResponse(
            id=store.id,
            name=store.name,
            location=store.location,
            lat=store.lat,
            lon=store.lon,
            manager=mgr_info,
            product_count=prod_count,
            active_stock=stock_sum
        ))

    return results


@router.post(
    "/branches",
    response_model=BranchDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new store branch and optionally assign a store manager (admin only)"
)
def create_admin_branch(
    request: BranchCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    new_store = Store(
        name=request.name.strip(),
        location=request.location.strip(),
        lat=request.lat or 0.0,
        lon=request.lon or 0.0
    )
    db.add(new_store)
    db.flush()

    mgr_info = None
    if request.manager_id:
        user = db.query(User).filter(User.id == request.manager_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {request.manager_id} not found."
            )
        if normalize_role(user.role) != "manager":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have the manager role."
            )
        if user.store_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Manager is already assigned to branch {user.store_id}."
            )
        user.store_id = new_store.id
        mgr_info = BranchManagerInfo(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email
        )

    db.commit()
    db.refresh(new_store)

    return BranchDetailResponse(
        id=new_store.id,
        name=new_store.name,
        location=new_store.location,
        lat=new_store.lat,
        lon=new_store.lon,
        manager=mgr_info,
        product_count=0,
        active_stock=0
    )


@router.get(
    "/analytics/global",
    response_model=GlobalAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Aggregated enterprise telemetry and branch performance metrics (admin only)"
)
def get_global_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    stores = db.query(Store).order_by(Store.id.asc()).all()
    total_stores = len(stores)

    total_products = db.query(func.count(Product.id)).scalar() or 0
    total_active_stock = (
        db.query(func.sum(ProductBatch.remaining_quantity))
        .filter(ProductBatch.remaining_quantity > 0)
        .scalar() or 0
    )

    waste_stats = db.query(
        func.sum(WasteLog.spoiled_quantity),
        func.sum(WasteLog.financial_loss)
    ).first()

    total_spoilage_units = waste_stats[0] or 0 if waste_stats else 0
    total_financial_loss = round(float(waste_stats[1] or 0.0), 2) if waste_stats else 0.0

    total_diverted_kg = round(max(0.0, float(total_active_stock * 0.45)), 1)

    store_summaries = []
    for s in stores:
        p_cnt = db.query(func.count(Product.id)).filter(Product.store_id == s.id).scalar() or 0
        s_stock = (
            db.query(func.sum(ProductBatch.remaining_quantity))
            .join(Product, Product.id == ProductBatch.product_id)
            .filter(Product.store_id == s.id, ProductBatch.remaining_quantity > 0)
            .scalar() or 0
        )
        s_loss = (
            db.query(func.sum(WasteLog.financial_loss))
            .filter(WasteLog.store_id == s.id)
            .scalar() or 0.0
        )
        store_summaries.append(StoreGlobalSummary(
            store_id=s.id,
            store_name=s.name,
            location=s.location,
            product_count=p_cnt,
            total_stock=s_stock,
            financial_loss=round(float(s_loss), 2)
        ))

    return GlobalAnalyticsResponse(
        total_stores=total_stores,
        total_products=total_products,
        total_active_stock=total_active_stock,
        total_spoilage_units=total_spoilage_units,
        total_financial_loss=total_financial_loss,
        total_diverted_kg=total_diverted_kg,
        stores=store_summaries
    )


@router.post(
    "/broadcast",
    response_model=BroadcastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish enterprise announcement or branch broadcast (admin only)"
)
def create_broadcast(
    request: BroadcastCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    if not request.title.strip() or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title and message cannot be empty."
        )

    store_name = None
    if request.target_store_id is not None:
        store = db.query(Store).filter(Store.id == request.target_store_id).first()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target store with ID {request.target_store_id} not found."
            )
        store_name = store.name

    author_name = current_user.get("name") or "System Administrator"

    broadcast = Broadcast(
        title=request.title.strip(),
        message=request.message.strip(),
        target_store_id=request.target_store_id,
        created_by=author_name,
        priority=request.priority or "normal"
    )
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)

    return BroadcastResponse(
        id=broadcast.id,
        title=broadcast.title,
        message=broadcast.message,
        target_store_id=broadcast.target_store_id,
        target_store_name=store_name,
        created_at=broadcast.created_at.isoformat(),
        created_by=broadcast.created_by,
        priority=broadcast.priority
    )
