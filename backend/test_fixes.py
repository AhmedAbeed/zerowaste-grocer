"""
test_fixes.py
Verification suite for targeted fixes (RBAC, unauthenticated prediction, batches/incoming, and audit validation).
"""
import uuid
from datetime import date, timedelta
from fastapi.testclient import TestClient
from main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.models import ProductBatch, Product

client = TestClient(app)

def test_rbac_denies():
    # Manager gets 403 on /inventory/audit
    mgr_token = create_access_token(data={"sub": "manager@zerowaste.com", "role": "manager", "role_id": "manager", "branch_id": 1, "store_id": 1})
    res_audit = client.post(
        "/api/v1/inventory/audit",
        json={"store_id": 1, "entries": [{"product_id": 1, "on_hand_qty": 20, "spoiled_qty": 0}]},
        headers={"Authorization": f"Bearer {mgr_token}"}
    )
    assert res_audit.status_code == 403, f"Expected 403 for manager on /inventory/audit, got {res_audit.status_code}"

    # Clerk gets 403 on /replenishment/approve
    clerk_token = create_access_token(data={"sub": "clerk@zerowaste.com", "role": "clerk", "role_id": "clerk", "branch_id": 1, "store_id": 1})
    res_approve = client.post(
        "/api/v1/replenishment/approve",
        json={"store_id": 1, "items": [{"product_id": 1, "final_qty": 10}]},
        headers={"Authorization": f"Bearer {clerk_token}"}
    )
    assert res_approve.status_code == 403, f"Expected 403 for clerk on /replenishment/approve, got {res_approve.status_code}"
    print("[PASS] manager gets 403 on /inventory/audit; clerk gets 403 on /replenishment/approve")

def test_prediction_auth():
    # /predict/demand without a token returns 401
    res_no_tok = client.post(
        "/api/v1/predict/demand",
        json={"store_id": 1, "product_id": 1, "lead_time": 0}
    )
    assert res_no_tok.status_code == 401, f"Expected 401 for /predict/demand without token, got {res_no_tok.status_code}"
    print("[PASS] /predict/demand without a token returns 401")

def test_batches_incoming_validation_and_duplicate():
    clerk_token = create_access_token(data={"sub": "clerk@zerowaste.com", "role": "clerk", "role_id": "clerk", "branch_id": 1, "store_id": 1})
    headers = {"Authorization": f"Bearer {clerk_token}"}
    future_date = (date.today() + timedelta(days=10)).isoformat()
    past_date = (date.today() - timedelta(days=10)).isoformat()

    # 1. Quantity 0 -> 422 or 400
    res_zero = client.post(
        "/api/v1/batches/incoming",
        json={"product_id": 1, "batch_id": "B-TEST-VALID-0", "quantity": 0, "expiration_date": future_date},
        headers=headers
    )
    assert res_zero.status_code in (400, 422), f"Expected 400/422 for qty 0, got {res_zero.status_code}"

    # 2. Past expiration -> 400
    res_past = client.post(
        "/api/v1/batches/incoming",
        json={"product_id": 1, "batch_id": "B-TEST-PAST", "quantity": 10, "expiration_date": past_date},
        headers=headers
    )
    assert res_past.status_code == 400, f"Expected 400 for past expiration, got {res_past.status_code}"

    # 3. Duplicate batch_id -> 409
    unique_bid = f"B-TEST-{uuid.uuid4().hex[:8]}"
    res_first = client.post(
        "/api/v1/batches/incoming",
        json={"product_id": 1, "batch_id": unique_bid, "quantity": 10, "expiration_date": future_date},
        headers=headers
    )
    assert res_first.status_code == 201, f"Initial batch insert failed: {res_first.status_code} {res_first.text}"

    res_dup = client.post(
        "/api/v1/batches/incoming",
        json={"product_id": 1, "batch_id": unique_bid, "quantity": 10, "expiration_date": future_date},
        headers=headers
    )
    assert res_dup.status_code == 409, f"Expected 409 on duplicate batch_id, got {res_dup.status_code}"
    assert "already exists" in res_dup.json()["detail"].lower()

    # Clean up test batch
    db = SessionLocal()
    try:
        db.query(ProductBatch).filter(ProductBatch.id == unique_bid).delete()
        db.commit()
    finally:
        db.close()

    print("[PASS] /batches/incoming: quantity 0 -> 422/400, past expiration -> 400, duplicate batch_id -> 409")

def test_audit_negative_on_hand_qty():
    auditor_token = create_access_token(data={"sub": "auditor@zerowaste.com", "role": "auditor", "role_id": "auditor", "branch_id": 1, "store_id": 1})
    headers = {"Authorization": f"Bearer {auditor_token}"}

    # Audit with negative on_hand_qty -> 422
    res_neg = client.post(
        "/api/v1/inventory/audit",
        json={"store_id": 1, "entries": [{"product_id": 1, "on_hand_qty": -5, "spoiled_qty": 0}]},
        headers=headers
    )
    assert res_neg.status_code == 422, f"Expected 422 for negative on_hand_qty, got {res_neg.status_code}"
    print("[PASS] audit with negative on_hand_qty -> 422")

if __name__ == "__main__":
    test_rbac_denies()
    test_prediction_auth()
    test_batches_incoming_validation_and_duplicate()
    test_audit_negative_on_hand_qty()
    print("\nALL TARGETED FIX TESTS PASSED SUCCESSFULLY!")
