"""
app/api/v1/endpoints/ai_ultra.py
Next-generation AI Ultra endpoints: demand forecasting, optimization recommendations, and discrepancy feedback.
"""
from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from scipy.stats import norm

from app.config import settings
from app.db.session import get_db
from app.models.models import Store, Product, ProductBatch, ModelFeedback
from app.schemas.api_schemas import (
    UltraForecastRequest,
    UltraForecastResponse,
    RecommendationsResponse,
    UltraFeedbackRequest,
    UltraFeedbackResponse
)
from app.core.security import require_roles, verify_branch_access
from app.services.reorder_service import (
    generate_store_recommendations,
    build_feature_dict,
    compute_rolling_sigma,
    _model,
    _feature_names,
    _translate_feature_label,
    MASTER_FEATURE_NAMES
)

router = APIRouter(prefix="/ai/ultra", tags=["ai-ultra"])

@router.post(
    "/forecast",
    response_model=UltraForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate high-precision demand forecast with confidence intervals and XAI drivers"
)
def ultra_forecast(
    request: UltraForecastRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("manager", "admin"))
):
    target_store_id = verify_branch_access(
        current_user,
        requested_store_id=request.store_id,
        require_for_admin=True
    )

    if request.target_date:
        try:
            target_dt = date.fromisoformat(request.target_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target_date format. Expected YYYY-MM-DD."
            )
    else:
        target_dt = settings.get_effective_today()

    product = (
        db.query(Product)
        .filter(Product.id == request.product_id, Product.store_id == target_store_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {request.product_id} not found in store {target_store_id}."
        )

    # Build 194-feature vector
    input_dict = build_feature_dict(db, target_store_id, product.id, target_dt, product=product)
    input_df = pd.DataFrame([input_dict], columns=MASTER_FEATURE_NAMES)

    raw_y = float(_model.predict(input_df)[0])
    y_hat = max(0.0, raw_y)
    predicted_units = max(1, int(round(y_hat * settings.DEMAND_SCALE)))

    # Compute rolling sigma
    sigma_e, sigma_source = compute_rolling_sigma(
        db, target_store_id, product.id, target_dt, predicted_units, product=product
    )

    # Newsvendor optimization for recommended order units
    cu = max(0.01, product.unit_price - product.unit_cost)
    salvage_val = product.unit_cost * settings.DEFAULT_SALVAGE_PCT
    co = max(0.01, product.unit_cost - salvage_val)
    cf = max(0.01, min(0.99, cu / (cu + co)))
    k = max(0.0, min(2.5, float(norm.ppf(cf))))
    optimal_buffer = max(product.safety_stock, int(round(k * sigma_e)))

    current_stock = sum(b.remaining_quantity for b in product.batches if b.remaining_quantity > 0)
    recommended_qty = max(0, predicted_units + optimal_buffer - current_stock)

    # TreeSHAP / pred_contrib attribution
    try:
        contribs = _model.predict(input_df, pred_contrib=True)[0]
    except Exception:
        if hasattr(_model, "booster_"):
            contribs = _model.booster_.predict(input_df, pred_contrib=True)[0]
        else:
            contribs = None

    top_drivers = []
    if contribs is not None and len(contribs) > 1:
        feat_contribs = contribs[:-1]
        abs_contribs = np.abs(feat_contribs)
        label_mags: Dict[str, float] = {}
        for fi, val in enumerate(abs_contribs):
            if fi < len(_feature_names):
                label = _translate_feature_label(_feature_names[fi])
                label_mags[label] = label_mags.get(label, 0.0) + float(val)

        sorted_labels = sorted(label_mags.items(), key=lambda kv: kv[1], reverse=True)[:3]
        total_mag = sum(v for _, v in sorted_labels) or 1.0
        for lbl, mag in sorted_labels:
            pct = round((mag / total_mag) * 100.0, 1)
            top_drivers.append({
                "factor": lbl,
                "impact_pct": pct,
                "magnitude": round(float(mag), 4)
            })

    confidence_interval = {
        "lower_95": max(0.0, round(predicted_units - 1.96 * sigma_e, 1)),
        "upper_95": round(predicted_units + 1.96 * sigma_e, 1),
        "sigma": sigma_e,
        "sigma_source": sigma_source
    }

    return UltraForecastResponse(
        product_id=product.id,
        product_name=product.name,
        store_id=target_store_id,
        target_date=target_dt.isoformat(),
        predicted_demand=float(predicted_units),
        recommended_order_units=recommended_qty,
        confidence_interval=confidence_interval,
        top_drivers=top_drivers
    )


@router.get(
    "/recommendations",
    response_model=RecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Ultra AI replenishment recommendations (manager and admin)"
)
def ultra_recommendations(
    store_id: Optional[int] = None,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("manager", "admin"))
):
    target_store_id = verify_branch_access(
        current_user,
        requested_store_id=store_id,
        require_for_admin=True
    )

    store = db.query(Store).filter(Store.id == target_store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {target_store_id} not found."
        )

    if target_date:
        try:
            target_dt = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target_date format. Expected YYYY-MM-DD."
            )
    else:
        target_dt = settings.get_effective_today()

    recs = generate_store_recommendations(db, store_id=target_store_id, target_date=target_dt)

    return RecommendationsResponse(
        store_id=target_store_id,
        target_date=target_dt.isoformat(),
        total_items=len(recs),
        items=recs
    )


@router.post(
    "/feedback",
    response_model=UltraFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record physical audit discrepancy feedback (auditor, manager, admin)"
)
def ultra_feedback(
    request: UltraFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("auditor", "manager", "admin"))
):
    target_store_id = verify_branch_access(
        current_user,
        requested_store_id=request.store_id,
        require_for_admin=True
    )

    if request.feedback_date:
        try:
            f_date = date.fromisoformat(request.feedback_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid feedback_date format. Expected YYYY-MM-DD."
            )
    else:
        f_date = settings.get_effective_today()

    product = (
        db.query(Product)
        .filter(Product.id == request.product_id, Product.store_id == target_store_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {request.product_id} not found in store {target_store_id}."
        )

    discrepancy_val = request.discrepancy
    if discrepancy_val is None and request.actual_demand is not None and request.predicted_demand is not None:
        discrepancy_val = round(request.actual_demand - request.predicted_demand, 2)

    feedback_record = ModelFeedback(
        store_id=target_store_id,
        product_id=product.id,
        feedback_date=f_date,
        predicted_demand=request.predicted_demand,
        actual_demand=request.actual_demand,
        spoiled_units=request.spoiled_units or 0,
        discrepancy=discrepancy_val,
        notes=request.notes
    )
    db.add(feedback_record)
    db.commit()
    db.refresh(feedback_record)

    return UltraFeedbackResponse(
        status="success",
        feedback_id=feedback_record.id,
        message=f"Discrepancy feedback recorded for product {product.id} on {f_date.isoformat()}."
    )
