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
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.broadcasts import router as broadcasts_router
from app.api.v1.endpoints.ai_ultra import router as ai_ultra_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(stores_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(replenishment_router)

# Direct alias for /reorders/approve
from app.api.v1.endpoints.replenishment import approve_recommendations
from app.schemas.api_schemas import ApprovalResponse
from fastapi import status
api_v1_router.add_api_route(
    "/reorders/approve",
    approve_recommendations,
    methods=["POST"],
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["replenishment"],
    summary="Alias for approving replenishment recommendations"
)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(prediction_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(broadcasts_router)
api_v1_router.include_router(ai_ultra_router)
