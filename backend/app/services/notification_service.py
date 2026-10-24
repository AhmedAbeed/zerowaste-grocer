"""
app/services/notification_service.py
Automated daily markdown notification and alert dismiss postponement service.
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.models.models import Store, ProductBatch, Notification, AlertAction
from app.services.alert_service import evaluate_store_spoilage_alerts


def is_batch_dismissed(db: Session, batch_id: str, now: Optional[datetime] = None) -> bool:
    """
    True if there is an AlertAction row with action == 'DISMISSED' for this batch
    and dismissed_until > now (evaluating the most recent row by created_at, id).
    """
    if now is None:
        now = datetime.now()

    action = (
        db.query(AlertAction)
        .filter(AlertAction.batch_id == batch_id, AlertAction.action == "DISMISSED")
        .order_by(AlertAction.created_at.desc(), AlertAction.id.desc())
        .first()
    )
    if action and action.dismissed_until and action.dismissed_until > now:
        return True
    return False


def run_daily_markdown_job(db: Session, now: Optional[datetime] = None) -> Dict[str, int]:
    """
    Evaluates spoilage markdown risks across all stores and generates daily notifications.
    De-duplicates per (store_id, batch_id, type, alert_date) and skips actively dismissed batches.
    """
    if now is None:
        now = datetime.now()
        alert_date = settings.get_effective_today()
    else:
        alert_date = now.date()

    stores = db.query(Store).order_by(Store.id.asc()).all()
    stores_processed = 0
    alerts_found = 0
    notifications_created = 0
    skipped_duplicates = 0
    skipped_dismissed = 0

    for store in stores:
        stores_processed += 1
        alerts = evaluate_store_spoilage_alerts(db, store_id=store.id, as_of_date=alert_date)
        alerts_found += len(alerts)

        for alert in alerts:
            if alert.get("status") == "accepted":
                continue
            batch_id = alert.get("batch_id")
            if not batch_id:
                parts = alert["id"].split("-")
                batch_id = "-".join(parts[2:]) if len(parts) >= 3 else alert["id"]

            if is_batch_dismissed(db, batch_id, now):
                skipped_dismissed += 1
                continue

            existing = (
                db.query(Notification)
                .filter(
                    Notification.store_id == store.id,
                    Notification.batch_id == batch_id,
                    Notification.type == "SPOILAGE_MARKDOWN",
                    Notification.alert_date == alert_date
                )
                .first()
            )
            if existing:
                skipped_duplicates += 1
                continue

            discount = int(round(alert["suggested_discount_pct"] * 100))
            remaining = alert["remaining_qty"]
            product_name = alert["product_name"]
            title = f"Spoilage risk: {product_name}"
            body = alert.get("suggestion_message") or f"Apply {discount}% discount to clear remaining {remaining} units today"

            notif = Notification(
                store_id=store.id,
                type="SPOILAGE_MARKDOWN",
                title=title,
                body=body,
                batch_id=batch_id,
                alert_date=alert_date,
                is_read=False,
                created_at=now
            )

            try:
                with db.begin_nested():
                    db.add(notif)
                    db.flush()
                notifications_created += 1
            except IntegrityError:
                skipped_duplicates += 1

    db.commit()

    summary = {
        "stores_processed": stores_processed,
        "alerts_found": alerts_found,
        "notifications_created": notifications_created,
        "skipped_duplicates": skipped_duplicates,
        "skipped_dismissed": skipped_dismissed
    }
    print(f"[SCHEDULER] markdown job: {summary}")
    return summary


def dismiss_batch(db: Session, batch_id: str, user_id: Optional[int], now: Optional[datetime] = None) -> datetime:
    """
    Dismisses a batch alert for DISMISS_POSTPONE_HOURS and logs to alert_actions audit log.
    Marks all unread notifications for that batch as read.
    """
    if now is None:
        now = datetime.now()

    batch = db.query(ProductBatch).filter(ProductBatch.id == batch_id).first()
    if not batch:
        batch = db.query(ProductBatch).filter(ProductBatch.id.contains(batch_id)).first()

    if not batch:
        raise ValueError(f"Batch with ID '{batch_id}' not found")

    store_id = batch.product.store_id
    dismissed_until = now + timedelta(hours=settings.DISMISS_POSTPONE_HOURS)

    action_entry = AlertAction(
        store_id=store_id,
        batch_id=batch.id,
        user_id=user_id,
        action="DISMISSED",
        dismissed_until=dismissed_until,
        created_at=now
    )
    db.add(action_entry)

    # Mark all unread Notification rows for that batch as is_read = True
    db.query(Notification).filter(
        Notification.batch_id == batch.id,
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)

    db.commit()
    return dismissed_until
