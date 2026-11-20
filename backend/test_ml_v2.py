import os
import sys
from pathlib import Path

BACKEND_DIR = Path(r"F:\Development\Projects\Mobile-Apps\backend")
sys.path.insert(0, str(BACKEND_DIR))

import joblib
import pandas as pd
import numpy as np
from datetime import date

from app.config import settings
from app.db.session import SessionLocal
from app.models.models import Product
from app.services.feature_builder import build_feature_vector, MASTER_FEATURE_NAMES
from app.services.ml_service import GroceryMLService, predict_grocery_demand, explain_prediction

def test_ml_upgrade():
    print("=" * 60)
    print("PHASE 1 VERIFICATION TEST: ML Upgrade (192 -> 194 Features)")
    print("=" * 60)

    # 1. Verify config
    print(f"1. EXPECTED_FEATURE_COUNT: {settings.EXPECTED_FEATURE_COUNT} (Expected: 194)")
    assert settings.EXPECTED_FEATURE_COUNT == 194

    # 2. Check loaded artifacts
    ml_svc = GroceryMLService.get_instance()
    model = ml_svc.model
    feature_names = ml_svc.master_feature_names

    print(f"2. Master features count: {len(feature_names)}")
    assert len(feature_names) == 194
    assert len(model.feature_name_) == 194

    # 3. Check diff and positions
    idx_7 = feature_names.index("sales_rolling_mean_7")
    idx_14 = feature_names.index("sales_rolling_mean_14")
    print(f"3. Feature positions:")
    print(f"   - sales_rolling_mean_7  at index {idx_7}")
    print(f"   - sales_rolling_mean_14 at index {idx_14}")
    print(f"   - Preceding feature: {feature_names[idx_7 - 1]}")
    print(f"   - Succeeding feature: {feature_names[idx_14 + 1]}")
    assert idx_7 == 180
    assert idx_14 == 181
    assert feature_names[179] == "lag_related_56"
    assert feature_names[182] == "store_id"

    # 4. Check feature_builder column order
    db = SessionLocal()
    try:
        p = db.query(Product).first()
        assert p is not None, "Product must exist in DB"
        store_id = p.store_id
        product_id = p.id
        today = settings.get_effective_today()

        vector_df = build_feature_vector(db, store_id=store_id, product_id=product_id, target_date=today)
        print(f"4. Feature vector generated shape: {vector_df.shape}")
        assert list(vector_df.columns) == list(model.feature_name_), "Feature vector columns MUST exactly match model.feature_name_"
        assert not vector_df.isna().any().any(), "Feature vector must NOT contain any NaNs"

        print(f"   sales_rolling_mean_7  value: {vector_df['sales_rolling_mean_7'].iloc[0]:.4f}")
        print(f"   sales_rolling_mean_14 value: {vector_df['sales_rolling_mean_14'].iloc[0]:.4f}")

        # 5. Run prediction
        raw_pred = float(model.predict(vector_df)[0])
        scaled_units = max(1, int(round(raw_pred * settings.DEMAND_SCALE)))
        print(f"5. Model Prediction:")
        print(f"   Raw prediction: {raw_pred:.4f}")
        print(f"   Scaled physical units (x{settings.DEMAND_SCALE}): {scaled_units} units")
        assert raw_pred > 0.0

        # 6. Run TreeSHAP explanation
        drivers = ml_svc.explain(store_id=store_id, product_id=product_id)
        print(f"6. TreeSHAP Explanations (Top 3):")
        for d in drivers:
            print(f"   - {d['label']}: {d['impact_pct']}%")
        assert len(drivers) == 3

        # 7. Check Objective
        booster_params = model.booster_.params
        print(f"7. Booster Objective: {booster_params.get('objective')} (metric: {booster_params.get('metric')})")

        print("\n>>> ALL PHASE 1 CHECKS PASSED SUCCESSFULLY! <<<")
    finally:
        db.close()

if __name__ == "__main__":
    test_ml_upgrade()
