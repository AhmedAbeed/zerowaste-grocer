"""
app/api/v1/endpoints/alerts.py
Dynamic spoilage markdown alert retrieval and POS synchronization endpoints.
"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.models.models import Store, ProductBatch
from datetime import datetime
from app.schemas.api_schemas import (
    AlertsListResponse,
    MarkdownActionRequest,
    MarkdownActionResponse,
    DismissAlertResponse,
    RunJobResponse
)
from app.services.notification_service import (
    is_batch_dismissed,
    run_daily_markdown_job,
    dismiss_batch
)
from app.services.alert_service import evaluate_store_spoilage_alerts
from app.core.security import get_current_user, require_roles

router = APIRouter(tags=["alerts"])

@router.get(
    "/alerts",
    response_model=AlertsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active spoilage markdown alerts"
)
def get_alerts(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("storeManager", "systemAdmin"))
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found"
        )

    alerts = evaluate_store_spoilage_alerts(db, store_id=store_id)
    now = datetime.now()
    active_alerts = []
    for a in alerts:
        b_id = a.get("batch_id")
        if not b_id:
            parts = a["id"].split("-")
            b_id = "-".join(parts[2:]) if len(parts) >= 3 else a["id"]
        if not is_batch_dismissed(db, b_id, now):
            active_alerts.append(a)

    open_alerts = [a for a in active_alerts if a.get("status") == "open"]
    units_at_risk = sum(a["remaining_qty"] for a in open_alerts)

    return AlertsListResponse(
        store_id=store_id,
        active_alerts_count=len(open_alerts),
        units_at_risk=units_at_risk,
        items=active_alerts
    )

@router.post(
    "/inventory/markdown",
    response_model=MarkdownActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply or dismiss dynamic markdown for expiring batch"
)
def action_markdown(
    request: MarkdownActionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("storeManager"))
):
    # Alert ID format: ALT-{store_id}-{batch_id}
    parts = request.alert_id.split("-")
    if len(parts) >= 3:
        batch_id = "-".join(parts[2:])
    else:
        batch_id = request.alert_id

    batch = db.query(ProductBatch).filter(ProductBatch.id == batch_id).first()
    if not batch:
        # Fallback partial search
        batch = db.query(ProductBatch).filter(ProductBatch.id.contains(batch_id)).first()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ProductBatch for alert {request.alert_id} not found"
        )

    today = settings.get_effective_today()
    days_to_expiry = max(0, (batch.expiration_date - today).days)

    if request.action == "accept":
        discount = 0.40 if days_to_expiry <= 1 else 0.25
        batch.current_discount_pct = discount
        db.commit()
        return MarkdownActionResponse(
            status="success",
            alert_id=request.alert_id,
            current_discount_pct=discount,
            message=f"Dynamic markdown of {int(discount * 100)}% applied to batch {batch.id}."
        )
    else:
        return MarkdownActionResponse(
            status="success",
            alert_id=request.alert_id,
            current_discount_pct=batch.current_discount_pct,
            message=f"Markdown alert {request.alert_id} dismissed."
        )

@router.post(
    "/alerts/run-now",
    response_model=RunJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Synchronously execute daily markdown job"
)
def run_now(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("storeManager", "systemAdmin"))
):
    result = run_daily_markdown_job(db)
    return RunJobResponse(**result)


@router.post(
    "/alerts/{batch_id}/dismiss",
    response_model=DismissAlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Dismiss an expiring batch alert for 6 hours"
)
def dismiss_alert(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("storeManager"))
):
    user_id_val = current_user.get("id") or current_user.get("sub")
    try:
        user_id = int(user_id_val) if user_id_val is not None else None
    except (ValueError, TypeError):
        user_id = None

    try:
        until = dismiss_batch(db, batch_id=batch_id, user_id=user_id)
        return DismissAlertResponse(
            batch_id=batch_id,
            dismissed_until=until.isoformat(),
            status="postponed"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
