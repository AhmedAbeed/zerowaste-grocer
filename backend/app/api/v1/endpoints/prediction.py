"""
app/api/v1/endpoints/prediction.py
FastAPI router for ML demand prediction and XAI drivers.
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.ml_schemas import PredictionRequest, PredictionResponse
from app.services.ml_service import predict_grocery_demand, explain_prediction

router = APIRouter(prefix="/predict", tags=["prediction"])

@router.post(
    "/demand",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Forecast grocery demand with XAI drivers",
    description="Accepts store_id, product_id, lead_time, and context features to generate a demand forecast and top 3 TreeSHAP drivers."
)
def predict_demand(request: PredictionRequest) -> PredictionResponse:
    try:
        predicted_demand = predict_grocery_demand(
            store_id=request.store_id,
            product_id=request.product_id,
            lead_time=request.lead_time,
            context_features=request.context_features
        )
        drivers = explain_prediction(
            store_id=request.store_id,
            product_id=request.product_id,
            lead_time=request.lead_time,
            context_features=request.context_features
        )
        return PredictionResponse(
            store_id=request.store_id,
            product_id=request.product_id,
            predicted_demand=predicted_demand,
            drivers=drivers
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )
