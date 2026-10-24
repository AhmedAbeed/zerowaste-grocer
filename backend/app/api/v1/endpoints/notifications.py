"""
app/api/v1/endpoints/notifications.py
Notification retrieval and status update endpoints (Store Manager only).
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Notification
from app.schemas.api_schemas import (
    NotificationListResponse,
    NotificationSchema,
    NotificationReadResponse
)
from app.core.security import require_roles

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List store notifications with unread count"
)
def get_notifications(
    store_id: int = Query(..., description="ID of the store"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    limit: int = Query(50, ge=1, le=200, description="Max notifications to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("storeManager"))
):
    # Total unread count for store, independent of unread_only and limit
    unread_count = (
        db.query(Notification)
        .filter(Notification.store_id == store_id, Notification.is_read == False)
        .count()
    )

    query = db.query(Notification).filter(Notification.store_id == store_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)

    rows = query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()

    items = [
        NotificationSchema(
            id=n.id,
            store_id=n.store_id,
            type=n.type,
            title=n.title,
            body=n.body,
            batch_id=n.batch_id,
            created_at=n.created_at.isoformat(),
            is_read=n.is_read
        )
        for n in rows
    ]

    return NotificationListResponse(items=items, unread_count=unread_count)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationReadResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a notification as read"
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("storeManager"))
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )

    notif.is_read = True
    db.commit()
    return NotificationReadResponse(id=notif.id, is_read=notif.is_read)
