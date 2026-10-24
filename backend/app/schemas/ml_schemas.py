"""
app/schemas/ml_schemas.py
Pydantic schemas for ML demand forecasting request, response, and explainability.
"""
from typing import Optional
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    store_id: int = Field(..., ge=1, le=3, description="Store identifier (1 to 3)")
    product_id: int = Field(..., ge=1, le=15, description="Product SKU identifier (1 to 15)")
    lead_time: int = Field(default=0, ge=0, description="Lead time window in days")
    context_features: Optional[dict[str, float]] = Field(
        default=None,
        description="Optional dynamic calendar or lag signals (e.g., lag_1, isWeekday)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "store_id": 1,
                "product_id": 10,
                "lead_time": 0,
                "context_features": {
                    "lag_1": 0.1553,
                    "isWeekday": 1.0
                }
            }
        }
    }

class XaiDriverSchema(BaseModel):
    label: str = Field(..., description="Feature name driver")
    impact_pct: float = Field(..., description="Attribution impact percentage")

class PredictionResponse(BaseModel):
    store_id: int = Field(..., description="Store location identifier")
    product_id: int = Field(..., description="Product SKU identifier")
    predicted_demand: float = Field(..., description="Non-negative forecasted demand volume")
    drivers: list[XaiDriverSchema] = Field(..., description="Top 3 XAI explanatory drivers")
