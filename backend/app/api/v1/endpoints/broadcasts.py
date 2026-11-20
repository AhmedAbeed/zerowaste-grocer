"""
app/api/v1/endpoints/broadcasts.py
Broadcast message retrieval endpoints for store managers and staff.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Broadcast, Store
from app.schemas.api_schemas import BroadcastResponse
from app.core.security import get_current_user, require_roles, normalize_role, get_user_branch_id

router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])

@router.get(
    "",
    response_model=List[BroadcastResponse],
    status_code=status.HTTP_200_OK,
    summary="List broadcast announcements for the user's branch"
)
def get_broadcasts(
    store_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    raw_role = current_user.get("role_id") or current_user.get("role", "")
    canonical_role = normalize_role(str(raw_role))

    if canonical_role == "admin":
        query = db.query(Broadcast)
        if store_id is not None:
            query = query.filter((Broadcast.target_store_id == store_id) | (Broadcast.target_store_id.is_(None)))
        broadcasts = query.order_by(Broadcast.created_at.desc()).all()
    else:
        # Branch-isolated for staff: manager, clerk, auditor
        user_branch = get_user_branch_id(current_user)
        if user_branch is None:
            user_branch = 1
        broadcasts = (
            db.query(Broadcast)
            .filter((Broadcast.target_store_id == user_branch) | (Broadcast.target_store_id.is_(None)))
            .order_by(Broadcast.created_at.desc())
            .all()
        )

    results = []
    for b in broadcasts:
        store_name = b.target_store.name if b.target_store else "All Branches"
        results.append(BroadcastResponse(
            id=b.id,
            title=b.title,
            message=b.message,
            target_store_id=b.target_store_id,
            target_store_name=store_name,
            created_at=b.created_at.isoformat(),
            created_by=b.created_by,
            priority=b.priority
        ))

    return results
