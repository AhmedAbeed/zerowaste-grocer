"""
test_b3.py
Deep verification test suite for ZeroWaste Grocer Level B3 mathematical services:
1. Strict 192-feature vector formulation
2. Newsvendor Critical Fractile replenishment recommendations
3. Dynamic Spoilage Markdown alert evaluation
"""
import sys
from datetime import date
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.session import SessionLocal
from app.services.feature_builder import build_feature_vector
from app.services.reorder_service import generate_store_recommendations
from app.services.alert_service import evaluate_store_spoilage_alerts

def run_tests():
    print("=" * 75)
    print("ZeroWaste Grocer - Level B3 Mathematical Services Verification")
    print("=" * 75)

    db = SessionLocal()
    today = date.today()

    try:
        # -------------------------------------------------------------
        # 1. Feature Vector Pipeline Test
        # -------------------------------------------------------------
        print("\n[Test 1/3] Verifying 192-Feature Engineering Pipeline...")
        df = build_feature_vector(db, store_id=1, product_id=1, target_date=today)

        print(f"      Feature matrix shape: {df.shape} (expected: (1, 192))")
        assert df.shape == (1, 192), f"Expected shape (1, 192), got {df.shape}"

        nan_count = df.isna().sum().sum()
        print(f"      NaN values count: {nan_count}")
        assert nan_count == 0, f"Found {nan_count} NaN values in feature matrix"

        # Check lag_1 through lag_56 non-zero
        lags = [df.at[0, f"lag_{i}"] for i in range(1, 57)]
        non_zero_lags = sum(1 for lag in lags if lag > 0.0)
        print(f"      Non-zero lags (1 to 56): {non_zero_lags}/56 (sample lag_1={lags[0]:.4f}, lag_7={lags[6]:.4f}, lag_56={lags[55]:.4f})")
        assert non_zero_lags == 56, f"All 56 lags must be non-zero, but found {non_zero_lags}"

        print("      [PASSED] 192-Feature Vector construction verified.")

        # -------------------------------------------------------------
        # 2. Newsvendor Replenishment Engine Test
        # -------------------------------------------------------------
        print("\n[Test 2/3] Verifying Newsvendor Critical Fractile Replenishment Engine...")
        recommendations = generate_store_recommendations(db, store_id=1, target_date=today)

        print(f"      Recommendations returned: {len(recommendations)} (expected: 15)")
        assert len(recommendations) == 15, f"Expected 15 recommendations, got {len(recommendations)}"

        print("\n" + "-" * 75)
        print(f"{'SKU / Product':<28} | {'Pred':<5} | {'Stock':<5} | {'Safe':<5} | {'Order':<5} | {'Top Driver'}")
        print("-" * 75)

        for rec in recommendations:
            assert rec["predicted_demand"] > 0, f"predicted_demand must be positive int, got {rec['predicted_demand']}"
            assert isinstance(rec["predicted_demand"], int), "predicted_demand must be int"
            assert rec["recommended_qty"] >= 0, f"recommended_qty must be >= 0, got {rec['recommended_qty']}"
            assert len(rec["xai_drivers"]) == 3, f"Expected 3 drivers, got {len(rec['xai_drivers'])}"

            driver_sum = sum(d["impact_pct"] for d in rec["xai_drivers"])
            assert abs(driver_sum - 100.0) <= 0.05, f"Driver impact percentages must sum to 100.0 (tolerance 0.05), got {driver_sum}"

            assert len(rec["xai_reason"]) > 0, "xai_reason must not be empty"

            top_drv = f"{rec['xai_drivers'][0]['label']} ({rec['xai_drivers'][0]['impact_pct']}%)"
            print(f"{rec['product_name'][:28]:<28} | {rec['predicted_demand']:<5} | {rec['current_stock']:<5} | {rec['safety_stock']:<5} | {rec['recommended_qty']:<5} | {top_drv}")

        # Check distinct XAI drivers across all 3 stores
        for sid in [1, 2, 3]:
            store_recs = recommendations if sid == 1 else generate_store_recommendations(db, store_id=sid, target_date=today)
            assert len(store_recs) == 15, f"Store {sid}: Expected 15 recommendations, got {len(store_recs)}"
            for rec in store_recs:
                assert len(rec["xai_drivers"]) == 3, f"Store {sid}: Expected exactly 3 drivers"
                labels = [d["label"] for d in rec["xai_drivers"]]
                assert len(set(labels)) == 3, f"Store {sid} product {rec['product_id']}: Drivers must be distinct, got {labels}"
                for d in rec["xai_drivers"]:
                    assert d["impact_pct"] >= 0, f"Store {sid}: Driver impact_pct must be >= 0, got {d['impact_pct']}"
                d_sum = sum(d["impact_pct"] for d in rec["xai_drivers"])
                assert abs(d_sum - 100.0) <= 0.05, f"Store {sid}: Driver impact percentages must sum to 100.0 within 0.05, got {d_sum}"

        print("-" * 75)
        print("      [PASSED] Newsvendor Replenishment Engine verified across all 3 stores.")

        # -------------------------------------------------------------
        # 3. Dynamic Spoilage Markdown Alert Engine Test
        # -------------------------------------------------------------
        print("\n[Test 3/3] Verifying Dynamic Spoilage Markdown Alert Engine...")
        alerts = evaluate_store_spoilage_alerts(db, store_id=1)

        print(f"      Spoilage alerts generated: {len(alerts)} (expected: >= 3)")
        assert len(alerts) >= 3, f"Expected at least 3 alerts, got {len(alerts)}"

        print("\n" + "-" * 75)
        print(f"{'Alert ID':<18} | {'Product Name':<26} | {'Expiry':<7} | {'Stock':<5} | {'Window':<6} | {'Markdown'}")
        print("-" * 75)

        alert_product_ids = [a["product_id"] for a in alerts]
        print(f"      Alert Product IDs: {alert_product_ids}")

        for alert in alerts:
            assert alert["status"] == "open", f"Alert status must be 'open', got {alert['status']}"
            assert alert["days_to_expiry"] <= 2, f"Days to expiry must be <= 2, got {alert['days_to_expiry']}"
            assert alert["remaining_qty"] > alert["predicted_demand"], f"Remaining qty {alert['remaining_qty']} must exceed predicted demand {alert['predicted_demand']}"
            expected_discount = 0.40 if alert["days_to_expiry"] <= 1 else 0.25
            assert alert["suggested_discount_pct"] == expected_discount, f"Expected discount {expected_discount}, got {alert['suggested_discount_pct']}"

            print(f"{alert['id']:<18} | {alert['product_name'][:26]:<26} | in {alert['days_to_expiry']}d   | {alert['remaining_qty']:<5} | {alert['predicted_demand']:<6} | -{int(alert['suggested_discount_pct']*100)}%")

        print("-" * 75)
        print("      [PASSED] Dynamic Spoilage Markdown Alert Engine verified.")

        print("\n" + "=" * 75)
        print("ALL LEVEL B3 TESTS AND ASSERTIONS PASSED SUCCESSFULLY!")
        print("=" * 75)

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
