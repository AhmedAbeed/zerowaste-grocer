"""
app/api/v1/__init__.py
Consolidated v1 API Router mounting all ZeroWaste Grocer endpoint routers.
"""
from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.stores import router as stores_router
from app.api.v1.endpoints.inventory import router as inventory_router
from app.api.v1.endpoints.replenishment import router as replenishment_router
from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.prediction import router as prediction_router
from app.api.v1.endpoints.notifications import router as notifications_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(stores_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(replenishment_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(prediction_router)
api_v1_router.include_router(notifications_router)
