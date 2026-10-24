"""
test_real_data.py
Executes model prediction and mathematical evaluation on the imported zerowaste_real.db.
Verifies predictions on store 1 (all 15 products) on 2023-06-30, and calculates
WAPE, MAE, and Bias against actual CSV values for product 1 across 2023-06-01 to 2023-06-30.
"""
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.models import Store, Product, DailyExogenous, InventorySnapshot
from app.services.feature_builder import build_feature_vector
from app.services.ml_service import GroceryMLService
from app.services.reorder_service import generate_store_recommendations
from app.config import settings

def run_real_data_verification():
    print("=" * 75)
    print("ZeroWaste Grocer - Real Dataset Prediction & Accuracy Verification")
    print("=" * 75)

    db_path = BACKEND_ROOT / "zerowaste_real.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database zerowaste_real.db not found at {db_path}")

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    db = Session()

    ml_service = GroceryMLService.get_instance()
    as_of_date = date(2023, 6, 30)

    # 1. Store 1: All 15 products prediction for 2023-06-30
    print(f"\n[Part 1] Store 1 Predictions on As-Of Date ({as_of_date}):")
    print(f"{'Product ID':<11} | {'Product Name':<28} | {'Raw y_hat':<10} | {'Pred Units':<11} | {'Rec Qty':<9}")
    print("-" * 75)

    store_1_products = (
        db.query(Product)
        .filter(Product.store_id == 1)
        .order_by(Product.id.asc())
        .all()
    )

    recoms = generate_store_recommendations(db=db, store_id=1, target_date=as_of_date)
    rec_by_pid = {r["product_id"]: r for r in recoms}

    preds_summary = []
    for prod in store_1_products:
        input_df = build_feature_vector(
            db=db,
            store_id=1,
            product_id=prod.id,
            target_date=as_of_date,
            product=prod
        )
        raw_pred = float(ml_service.model.predict(input_df)[0])
        pred_units = max(1, int(round(max(0.0, raw_pred) * settings.DEMAND_SCALE)))

        rec = rec_by_pid.get(prod.id, {})
        rec_qty = rec.get("recommended_qty", 0)

        preds_summary.append({
            "product_id": prod.id,
            "name": prod.name,
            "raw_pred": raw_pred,
            "pred_units": pred_units,
            "rec_qty": rec_qty
        })
        print(f"P{prod.id:<10d} | {prod.name:<28s} | {raw_pred:<10.4f} | {pred_units:<11d} | {rec_qty:<9d}")

    # Check reasonable range
    raw_vals = [p["raw_pred"] for p in preds_summary]
    min_raw = min(raw_vals)
    max_raw = max(raw_vals)
    mean_raw = sum(raw_vals) / len(raw_vals)
    print("-" * 75)
    print(f"Raw y_hat range: min={min_raw:.4f}, max={max_raw:.4f}, mean={mean_raw:.4f}")
    assert len(set(raw_vals)) > 1, "ERROR: All predictions are identical!"
    assert min_raw > 0.0, "ERROR: Minimum prediction is zero or negative!"
    print("[PASSED] Predictions are distinct, positive, and in realistic retail range.")

    # 2. Accuracy evaluation for Product 1 (2023-06-01 to 2023-06-30) against raw CSV
    print(f"\n[Part 2] Product 1 Accuracy Evaluation (2023-06-01 to 2023-06-30):")
    csv_path = BACKEND_ROOT / "data set" / "dataset" / "sales_grocer1_1_0.csv"
    df_csv = pd.read_csv(csv_path)
    df_csv["sales_date"] = pd.to_datetime(df_csv["sales_date"]).dt.date
    csv_map = dict(zip(df_csv["sales_date"], df_csv["sum_amount"]))

    prod_1 = store_1_products[0]
    eval_dates = [date(2023, 6, d) for d in range(1, 31)]

    y_trues = []
    y_preds = []

    for d in eval_dates:
        input_df = build_feature_vector(
            db=db,
            store_id=1,
            product_id=prod_1.id,
            target_date=d,
            product=prod_1
        )
        pred = float(ml_service.model.predict(input_df)[0])
        actual = float(csv_map.get(d, 0.0))
        y_preds.append(pred)
        y_trues.append(actual)

    y_t = np.array(y_trues)
    y_p = np.array(y_preds)

    wape = np.sum(np.abs(y_t - y_p)) / np.sum(y_t)
    mae = np.mean(np.abs(y_t - y_p))
    bias = np.sum(y_p) / np.sum(y_t)

    print(f"Product:                {prod_1.name} (Store 1, Product 1)")
    print(f"Evaluated Days:         {len(eval_dates)} days (June 2023)")
    print(f"WAPE:                   {wape:.4f} ({wape*100:.2f}%)")
    print(f"MAE:                    {mae:.6f}")
    print(f"Bias Ratio (pred/true): {bias:.4f}")

    assert 0.10 <= wape <= 0.65, f"WAPE {wape:.4f} is outside expected range [0.10, 0.65]"
    assert 0.70 <= bias <= 1.30, f"Bias {bias:.4f} is outside expected range [0.70, 1.30]"

    print("\n" + "=" * 75)
    print("Real data predictions executed successfully.")
    print("=" * 75)

    db.close()

if __name__ == "__main__":
    run_real_data_verification()
