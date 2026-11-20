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
    AuditSubmitResponse,
    IncomingBatchRequest,
    IncomingBatchResponse
)
from app.core.security import get_current_user, require_roles, verify_branch_access

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
    target_store_id = verify_branch_access(current_user, store_id)
    store = db.query(Store).filter(Store.id == target_store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {target_store_id} not found"
        )

    products = (
        db.query(Product)
        .filter(Product.store_id == target_store_id)
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
    verify_branch_access(current_user, product.store_id)

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
    current_user: dict = Depends(require_roles("auditor"))
):
    target_store_id = verify_branch_access(current_user, request.store_id)
    today = settings.get_effective_today()
    updated = 0

    for entry in request.entries:
        prod = db.query(Product).filter(Product.id == entry.product_id, Product.store_id == target_store_id).first()
        if not prod:
            continue

        # Record waste if spoiled units reported
        if entry.spoiled_qty > 0:
            loss = round(entry.spoiled_qty * prod.unit_cost, 2)
            waste = WasteLog(
                product_id=prod.id,
                store_id=target_store_id,
                date=today,
                spoiled_quantity=entry.spoiled_qty,
                financial_loss=loss,
                recorded_by=current_user.get("name", "Inventory Auditor")
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


@router.post(
    "/batches/incoming",
    response_model=IncomingBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register incoming product shipment/batch and update active stock (clerk only)"
)
def register_incoming_batch(
    request: IncomingBatchRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("clerk"))
):
    target_store_id = verify_branch_access(current_user)
    today = settings.get_effective_today()
    real_today = date.today()

    if request.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch quantity must be greater than 0."
        )

    if request.expiration_date <= today or request.expiration_date <= real_today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiration date must be in the future."
        )

    clean_batch_id = request.batch_id.strip()
    if not clean_batch_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch ID cannot be empty."
        )

    # 1. Product must belong to the clerk's branch
    product = (
        db.query(Product)
        .filter(Product.id == request.product_id, Product.store_id == target_store_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {request.product_id} not found in branch {target_store_id}."
        )

    # 2. Batch ID must be globally unique across all branches (reject duplicates with 409)
    duplicate_batch = (
        db.query(ProductBatch)
        .filter(ProductBatch.id == clean_batch_id)
        .first()
    )
    if duplicate_batch:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch ID already exists"
        )

    # 3. Create batch and update stock in the SAME transaction
    new_batch = ProductBatch(
        id=clean_batch_id,
        product_id=product.id,
        received_date=today,
        expiration_date=request.expiration_date,
        initial_quantity=request.quantity,
        remaining_quantity=request.quantity,
        current_discount_pct=0.0
    )
    db.add(new_batch)

    # Update or create InventorySnapshot for today
    snap = (
        db.query(InventorySnapshot)
        .filter(
            InventorySnapshot.product_id == product.id,
            InventorySnapshot.snapshot_date == today
        )
        .first()
    )
    if snap:
        snap.closing_stock += request.quantity
    else:
        snap = InventorySnapshot(
            product_id=product.id,
            snapshot_date=today,
            opening_stock=request.quantity,
            units_sold=0,
            units_spoiled=0,
            closing_stock=request.quantity
        )
        db.add(snap)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch ID already exists"
        )
    db.refresh(new_batch)

    # Active stock across all batches
    active_stock = sum(b.remaining_quantity for b in product.batches if b.remaining_quantity > 0)

    return IncomingBatchResponse(
        status="success",
        batch_id=new_batch.id,
        product_id=product.id,
        product_name=product.name,
        store_id=target_store_id,
        quantity=new_batch.remaining_quantity,
        expiration_date=new_batch.expiration_date.isoformat(),
        current_stock=active_stock,
        message=f"Batch {new_batch.id} added with {new_batch.remaining_quantity} units. Stock updated."
    )

