"""
app/services/alert_service.py
Dynamic Spoilage Markdown Alert Engine for ZeroWaste Grocer.
Evaluates expiring inventory batches against ML forecasted demand and
generates automated dynamic markdown salvage recommendations.
"""
from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import Product, ProductBatch
from app.services.feature_builder import build_feature_vector
from app.services.ml_service import GroceryMLService

_ml_service = GroceryMLService.get_instance()
_model = _ml_service.model

def evaluate_store_spoilage_alerts(
    db: Session,
    store_id: int,
    as_of_date: date | None = None
) -> List[Dict[str, Any]]:
    """
    Evaluates batches expiring within 2 days for the given store and triggers
    salvage markdown alerts when remaining quantity exceeds remaining window demand.
    """
    today = as_of_date or settings.get_effective_today()

    expiring_batches = (
        db.query(ProductBatch)
        .join(Product, ProductBatch.product_id == Product.id)
        .filter(
            Product.store_id == store_id,
            ProductBatch.remaining_quantity > 0,
            ProductBatch.expiration_date <= today + timedelta(days=2)
        )
        .order_by(ProductBatch.expiration_date.asc())
        .all()
    )

    alerts = []
    daily_predictions: Dict[int, int] = {}

    for batch in expiring_batches:
        prod = batch.product
        days_to_expiry = max(0, (batch.expiration_date - today).days)

        if prod.id not in daily_predictions:
            input_df = build_feature_vector(db, store_id, prod.id, today)
            raw_y = float(_model.predict(input_df)[0])
            daily_demand = max(1, int(round(max(0.0, raw_y) * settings.DEMAND_SCALE)))
            daily_predictions[prod.id] = daily_demand
        else:
            daily_demand = daily_predictions[prod.id]

        window_demand = max(1, daily_demand * max(1, days_to_expiry))

        # Spoilage risk: batch expires within 2 days AND remaining units exceed predicted demand over the remaining shelf life
        if batch.remaining_quantity > window_demand:
            if days_to_expiry <= 1:
                suggested_discount = 0.40
            else:
                suggested_discount = 0.25

            is_accepted = (batch.current_discount_pct or 0.0) > 0
            alert_item = {
                "id": f"ALT-{store_id}-{batch.id}",
                "batch_id": batch.id,
                "product_id": prod.id,
                "product_name": prod.name,
                "days_to_expiry": days_to_expiry,
                "remaining_qty": batch.remaining_quantity,
                "predicted_demand": window_demand,
                "suggested_discount_pct": suggested_discount,
                "status": "accepted" if is_accepted else "open"
            }
            if is_accepted:
                alert_item["applied_discount_pct"] = batch.current_discount_pct
            alerts.append(alert_item)

    return alerts
