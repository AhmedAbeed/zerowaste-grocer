import warnings
warnings.filterwarnings('ignore')
"""
test_ml.py
Verification script for ZeroWaste Grocer ML pipeline and FastAPI endpoint.
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.ml_service import (
    GroceryMLService,
    predict_grocery_demand,
    explain_prediction
)
from app.schemas.ml_schemas import PredictionRequest, PredictionResponse
from fastapi.testclient import TestClient
from main import app

def run_tests():
    print("=" * 60)
    print("ZeroWaste Grocer - ML Pipeline & API Verification")
    print("=" * 60)

    # 1. Verify ML Service singleton & Feature Count
    service = GroceryMLService.get_instance()
    print(f"[OK] ML Service initialized successfully.")
    print(f"[OK] Master feature names count: {len(service.master_feature_names)} (expected 192)")
    assert len(service.master_feature_names) == 192, "Feature count must be exactly 192"

    # 2. Test direct inference function
    test_store_id = 1
    test_product_id = 10
    test_lead_time = 0
    test_context = {
        "lag_1": 0.1553,
        "isWeekday": 1.0
    }

    predicted_demand = predict_grocery_demand(
        store_id=test_store_id,
        product_id=test_product_id,
        lead_time=test_lead_time,
        context_features=test_context
    )

    print(f"[OK] Direct prediction result: {predicted_demand} (type: {type(predicted_demand).__name__})")
    assert isinstance(predicted_demand, float), "Prediction must return a float"
    assert predicted_demand >= 0.0, "Prediction must be non-negative"

    # 3. Test XAI TreeSHAP explainability
    drivers = explain_prediction(
        store_id=test_store_id,
        product_id=test_product_id,
        lead_time=test_lead_time,
        context_features=test_context
    )
    print(f"[OK] Explainability drivers ({len(drivers)} drivers extracted):")
    for d in drivers:
        print(f"     - Feature: {d['label']}, Impact: {d['impact_pct']}%")
    assert len(drivers) == 3, "Explainability must return top 3 drivers"
    for d in drivers:
        assert "label" in d and "impact_pct" in d
        assert isinstance(d["impact_pct"], (int, float))

    # 4. Test FastAPI TestClient
    client = TestClient(app)

    # Health check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f"[OK] GET /health response: {health_data}")
    assert health_data == {"status": "healthy", "service": "zerowaste-api"}

    # Demand prediction POST
    payload = {
        "store_id": test_store_id,
        "product_id": test_product_id,
        "lead_time": test_lead_time,
        "context_features": test_context
    }
    pred_resp = client.post("/api/v1/predict/demand", json=payload)
    assert pred_resp.status_code == 200, f"Prediction API failed: {pred_resp.text}"
    pred_data = pred_resp.json()
    print(f"[OK] POST /api/v1/predict/demand response:")
    print(f"     Store ID: {pred_data['store_id']}")
    print(f"     Product ID: {pred_data['product_id']}")
    print(f"     Predicted Demand: {pred_data['predicted_demand']}")
    print(f"     Drivers: {pred_data['drivers']}")

    assert pred_data["store_id"] == 1
    assert pred_data["product_id"] == 10
    assert pred_data["predicted_demand"] >= 0.0
    assert len(pred_data["drivers"]) == 3

    print("=" * 60)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
