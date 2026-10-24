"""
app/api/v1/endpoints/replenishment.py
AI-recommended replenishment generation and purchase order approval endpoints.
"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.models.models import Store, Product, ReplenishmentOrder, OrderItem
from app.schemas.api_schemas import (
    RecommendationsResponse,
    ApprovalRequest,
    ApprovalResponse
)
from app.services.reorder_service import generate_store_recommendations
from app.core.security import get_current_user, require_roles

router = APIRouter(prefix="/replenishment", tags=["replenishment"])

@router.get(
    "/recommendations",
    response_model=RecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI replenishment recommendations with Explainable AI drivers"
)
def get_recommendations(
    store_id: int,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("storeManager", "systemAdmin"))
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found"
        )

    if target_date:
        try:
            target_dt = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target_date format. Expected YYYY-MM-DD."
            )
    else:
        target_dt = settings.get_effective_today()

    effective_today = settings.get_effective_today()
    approved_product_ids = set(
        p_id for (p_id,) in (
            db.query(OrderItem.product_id)
            .join(ReplenishmentOrder, ReplenishmentOrder.id == OrderItem.order_id)
            .filter(
                ReplenishmentOrder.store_id == store_id,
                ReplenishmentOrder.order_date == effective_today,
                ReplenishmentOrder.status == "APPROVED"
            )
            .all()
        )
    )

    recs = generate_store_recommendations(db, store_id=store_id, target_date=target_dt)
    for r in recs:
        is_app = r["product_id"] in approved_product_ids
        r["approved"] = is_app
        if is_app:
            r["status"] = "approved"

    return RecommendationsResponse(
        store_id=store_id,
        target_date=target_dt.isoformat(),
        total_items=len(recs),
        items=recs
    )

@router.post(
    "/approve",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Approve or adjust replenishment order and dispatch to supplier"
)
def approve_recommendations(
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("storeManager"))
):
    store = db.query(Store).filter(Store.id == request.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {request.store_id} not found"
        )

    today = settings.get_effective_today()
    delivery = today + timedelta(days=1)

    already_approved_ids = set(
        p_id for (p_id,) in (
            db.query(OrderItem.product_id)
            .join(ReplenishmentOrder, ReplenishmentOrder.id == OrderItem.order_id)
            .filter(
                ReplenishmentOrder.store_id == request.store_id,
                ReplenishmentOrder.order_date == today,
                ReplenishmentOrder.status == "APPROVED"
            )
            .all()
        )
    )

    total_units = 0
    total_amount = 0.0
    first_order_id = 0
    actually_created_count = 0

    for item in request.items:
        if item.product_id in already_approved_ids:
            continue

        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if not prod:
            continue

        cost = round(prod.unit_cost * item.final_qty, 2)
        total_amount += cost
        total_units += item.final_qty

        order = ReplenishmentOrder(
            store_id=request.store_id,
            order_date=today,
            delivery_date=delivery,
            status="APPROVED",
            total_amount=cost
        )
        db.add(order)
        db.flush()
        if not first_order_id:
            first_order_id = order.id
        actually_created_count += 1
        already_approved_ids.add(item.product_id)

        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            predicted_demand=float(item.final_qty),
            recommended_qty=item.final_qty,
            final_approved_qty=item.final_qty,
            xai_reason=item.override_reason or "Approved replenishment quantity"
        )
        db.add(order_item)

    db.commit()

    return ApprovalResponse(
        status="success",
        order_id=first_order_id or 1,
        approved_items_count=actually_created_count,
        total_units=total_units
    )
