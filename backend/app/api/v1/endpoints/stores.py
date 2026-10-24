"""
app/api/v1/endpoints/stores.py
Store entity management and lookup endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Store
from app.schemas.api_schemas import StoreResponse, StoreCreateRequest
from app.core.security import get_current_user, require_roles

router = APIRouter(prefix="/stores", tags=["stores"])

@router.get(
    "",
    response_model=List[StoreResponse],
    status_code=status.HTTP_200_OK,
    summary="List all active stores"
)
def get_stores(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    stores = db.query(Store).order_by(Store.id.asc()).all()
    return [
        StoreResponse(id=s.id, name=s.name, location=s.location)
        for s in stores
    ]


@router.post(
    "",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new retail store branch (System Admin only)"
)
def create_store(
    request: StoreCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("systemAdmin"))
):
    new_store = Store(
        name=request.name,
        location=request.location,
        lat=request.lat,
        lon=request.lon
    )
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    return StoreResponse(id=new_store.id, name=new_store.name, location=new_store.location)
