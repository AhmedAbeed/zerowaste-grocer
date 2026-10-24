"""
app/api/v1/endpoints/inventory.py
Inventory catalog lookup, batch tracking, and physical audit submission endpoints.
"""
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.models.models import Store, Product, ProductBatch, InventorySnapshot, WasteLog
from app.schemas.api_schemas import (
    InventoryResponse,
    ProductResponse,
    BatchResponse,
    AuditSubmitRequest,
    AuditSubmitResponse
)
from app.core.security import get_current_user, require_roles

router = APIRouter(tags=["inventory"])

@router.get(
    "/stores/{store_id}/inventory",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active store inventory catalog"
)
def get_store_inventory(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found"
        )

    products = (
        db.query(Product)
        .filter(Product.store_id == store_id)
        .order_by(Product.id.asc())
        .all()
    )

    items = []
    for p in products:
        # Sum active batch quantities
        stock = sum(b.remaining_quantity for b in p.batches if b.remaining_quantity > 0)
        if stock == 0:
            latest_snap = (
                db.query(InventorySnapshot)
                .filter(InventorySnapshot.product_id == p.id)
                .order_by(InventorySnapshot.snapshot_date.desc())
                .first()
            )
            stock = latest_snap.closing_stock if latest_snap else p.safety_stock

        category_str = p.category.name.lower() if p.category else "produce"

        items.append(ProductResponse(
            id=p.id,
            sku=p.sku,
            name=p.name,
            category=category_str,
            unit_cost=p.unit_cost,
            unit_price=p.unit_price,
            shelf_life_days=p.shelf_life_days,
            safety_stock=p.safety_stock,
            current_stock=stock
        ))

    return InventoryResponse(
        store_id=store.id,
        store_name=store.name,
        items=items
    )

@router.get(
    "/products/{product_id}/batches",
    response_model=List[BatchResponse],
    status_code=status.HTTP_200_OK,
    summary="Get batches for a specific product"
)
def get_product_batches(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    batches = (
        db.query(ProductBatch)
        .filter(ProductBatch.product_id == product_id)
        .order_by(ProductBatch.expiration_date.asc())
        .all()
    )

    today = settings.get_effective_today()
    return [
        BatchResponse(
            id=b.id,
            product_id=b.product_id,
            received_date=b.received_date.isoformat(),
            expiration_date=b.expiration_date.isoformat(),
            remaining_qty=b.remaining_quantity,
            discount_pct=b.current_discount_pct,
            days_to_expiry=max(0, (b.expiration_date - today).days)
        )
        for b in batches
    ]

@router.post(
    "/inventory/audit",
    response_model=AuditSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit end-of-day physical stock count and waste verification audit"
)
def submit_inventory_audit(
    request: AuditSubmitRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("inventoryAuditor", "storeManager", "systemAdmin"))
):
    today = settings.get_effective_today()
    updated = 0

    for entry in request.entries:
        prod = db.query(Product).filter(Product.id == entry.product_id).first()
        if not prod:
            continue

        # Record waste if spoiled units reported
        if entry.spoiled_qty > 0:
            loss = round(entry.spoiled_qty * prod.unit_cost, 2)
            waste = WasteLog(
                product_id=prod.id,
                store_id=request.store_id,
                date=today,
                spoiled_quantity=entry.spoiled_qty,
                financial_loss=loss,
                recorded_by=current_user.get("name", "Store Manager")
            )
            db.add(waste)

        # Update or create InventorySnapshot for today
        snap = (
            db.query(InventorySnapshot)
            .filter(
                InventorySnapshot.product_id == prod.id,
                InventorySnapshot.snapshot_date == today
            )
            .first()
        )
        if snap:
            snap.closing_stock = entry.on_hand_qty
            snap.units_spoiled += entry.spoiled_qty
        else:
            snap = InventorySnapshot(
                product_id=prod.id,
                snapshot_date=today,
                opening_stock=entry.on_hand_qty + entry.spoiled_qty,
                units_sold=0,
                units_spoiled=entry.spoiled_qty,
                closing_stock=entry.on_hand_qty
            )
            db.add(snap)

        # Reconcile product batches with audit on-hand count across all batches
        active_batches = (
            db.query(ProductBatch)
            .filter(ProductBatch.product_id == prod.id, ProductBatch.remaining_quantity > 0)
            .order_by(ProductBatch.expiration_date.asc())
            .all()
        )
        total_before = sum(b.remaining_quantity for b in active_batches)
        delta = entry.on_hand_qty - total_before

        if delta < 0:
            units_to_remove = -delta
            for b in active_batches:
                if units_to_remove <= 0:
                    break
                deduct = min(b.remaining_quantity, units_to_remove)
                b.remaining_quantity -= deduct
                units_to_remove -= deduct
        elif delta > 0:
            if active_batches:
                latest_batch = max(active_batches, key=lambda b: b.expiration_date)
                latest_batch.remaining_quantity += delta
            else:
                any_batch = (
                    db.query(ProductBatch)
                    .filter(ProductBatch.product_id == prod.id)
                    .order_by(ProductBatch.expiration_date.desc())
                    .first()
                )
                if any_batch:
                    any_batch.remaining_quantity += delta

        updated += 1

    db.commit()

    return AuditSubmitResponse(
        status="success",
        updated_count=updated,
        message=f"Audit completed successfully for {updated} items."
    )
