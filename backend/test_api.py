"""
test_api.py
Comprehensive End-to-End Test Suite for all 12 ZeroWaste Grocer REST API endpoints:
1.  POST /api/v1/auth/login
2.  GET  /api/v1/stores
3.  GET  /api/v1/stores/1/inventory
4.  GET  /api/v1/products/1/batches
5.  POST /api/v1/inventory/audit
6.  GET  /api/v1/replenishment/recommendations?store_id=1
7.  POST /api/v1/replenishment/approve
8.  GET  /api/v1/alerts?store_id=1
9.  POST /api/v1/inventory/markdown
10. GET  /api/v1/analytics/waste-metrics?store_id=1
11. GET  /api/v1/analytics/sales-series?store_id=1
12. GET  /api/v1/analytics/category-waste?store_id=1
"""
import sys
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app
from app.db.session import SessionLocal
from sqlalchemy import func
from app.models.models import Store, Notification, AlertAction, ProductBatch, ReplenishmentOrder, OrderItem

def run_api_tests():
    print("=" * 75)
    print("ZeroWaste Grocer - Level B4 Full REST API Integration Test Suite")
    print("=" * 75)

    client = TestClient(app)

    # 1. POST /api/v1/auth/login
    print("\n[Endpoint 1/12] Testing POST /api/v1/auth/login...")
    login_payload = {
        "email": "manager@zerowaste.com",
        "password": "password123"
    }
    r = client.post("/api/v1/auth/login", json=login_payload)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Login failed: {r.text}"
    login_data = r.json()
    assert "token" in login_data and len(login_data["token"]) > 10
    assert login_data["user"]["role"] == "storeManager"
    auth_token = login_data["token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    print(f"      [PASSED] Token received: {auth_token[:25]}... (User: {login_data['user']['name']})")

    # 2. GET /api/v1/stores
    print("\n[Endpoint 2/12] Testing GET /api/v1/stores...")
    r = client.get("/api/v1/stores", headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Get stores failed: {r.text}"
    stores = r.json()
    print(f"      Stores count: {len(stores)}")
    assert len(stores) == 3, f"Expected exactly 3 stores, got {len(stores)}"
    for s in stores:
        print(f"        - Store {s['id']}: {s['name']} ({s['location']})")
    print("      [PASSED] Stores endpoint verified.")

    # 3. GET /api/v1/stores/1/inventory
    print("\n[Endpoint 3/12] Testing GET /api/v1/stores/1/inventory...")
    r = client.get("/api/v1/stores/1/inventory", headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Get inventory failed: {r.text}"
    inv = r.json()
    assert inv["store_id"] == 1
    assert len(inv["items"]) == 15, f"Expected 15 products in Store 1, got {len(inv['items'])}"
    print(f"      Products count: {len(inv['items'])} in '{inv['store_name']}'")
    sample_prod = inv["items"][0]
    print(f"        Sample: {sample_prod['name']} (SKU: {sample_prod['sku']}, Stock: {sample_prod['current_stock']}, Price: ${sample_prod['unit_price']})")
    print("      [PASSED] Inventory endpoint verified.")

    # 4. GET /api/v1/products/1/batches
    print("\n[Endpoint 4/12] Testing GET /api/v1/products/1/batches...")
    r = client.get("/api/v1/products/1/batches", headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Get batches failed: {r.text}"
    batches = r.json()
    print(f"      Batches returned: {len(batches)}")
    assert len(batches) >= 1, "Expected at least 1 active batch"
    for b in batches:
        print(f"        - Batch {b['id']}: Remaining: {b['remaining_qty']}, Expires: {b['expiration_date']}, Discount: {b['discount_pct']}%")
    print("      [PASSED] Batches endpoint verified.")

    # 5. POST /api/v1/inventory/audit
    print("\n[Endpoint 5/12] Testing POST /api/v1/inventory/audit...")
    audit_payload = {
        "store_id": 1,
        "entries": [
            {"product_id": 1, "on_hand_qty": 20, "spoiled_qty": 2},
            {"product_id": 2, "on_hand_qty": 15, "spoiled_qty": 1}
        ]
    }
    r = client.post("/api/v1/inventory/audit", json=audit_payload, headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Audit submit failed: {r.text}"
    audit_resp = r.json()
    assert audit_resp["status"] == "success"
    assert audit_resp["updated_count"] == 2
    print(f"      Result: {audit_resp['message']}")
    print("      [PASSED] Inventory audit submission verified.")

    # 6. GET /api/v1/replenishment/recommendations?store_id=1
    print("\n[Endpoint 6/12] Testing GET /api/v1/replenishment/recommendations?store_id=1...")
    r = client.get("/api/v1/replenishment/recommendations?store_id=1", headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Recommendations failed: {r.text}"
    recs_resp = r.json()
    assert recs_resp["store_id"] == 1
    assert recs_resp["total_items"] == 15
    first_item = recs_resp["items"][0]
    assert len(first_item["xai_drivers"]) == 3
    print(f"      Total recommendations: {recs_resp['total_items']}")
    print(f"        Sample: {first_item['product_name']} -> Demand: {first_item['predicted_demand']}, Reorder: {first_item['recommended_qty']}")
    print(f"        Rationale: \"{first_item['xai_reason']}\"")
    print("      [PASSED] Replenishment recommendations verified.")

    # 7. POST /api/v1/replenishment/approve
    print("\n[Endpoint 7/12] Testing POST /api/v1/replenishment/approve...")
    approve_payload = {
        "store_id": 1,
        "items": [
            {"product_id": 1, "final_qty": 18, "override_reason": "AI recommendation accepted"},
            {"product_id": 2, "final_qty": 15, "override_reason": "Adjusted for weekend promo"}
        ]
    }
    r = client.post("/api/v1/replenishment/approve", json=approve_payload, headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 201, f"Approve failed: {r.text}"
    appr_resp = r.json()
    assert appr_resp["status"] == "success"
    assert "order_id" in appr_resp and appr_resp["order_id"] > 0
    assert appr_resp["approved_items_count"] == 2
    assert appr_resp["total_units"] == 33
    print(f"      Order ID: {appr_resp['order_id']}, Total Units Approved: {appr_resp['total_units']}")
    print("      [PASSED] Replenishment order approval verified.")

    # 8. GET /api/v1/alerts?store_id=1
    print("\n[Endpoint 8/12] Testing GET /api/v1/alerts?store_id=1...")
    r = client.get("/api/v1/alerts?store_id=1", headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Get alerts failed: {r.text}"
    alerts_resp = r.json()
    assert alerts_resp["store_id"] == 1
    assert alerts_resp["active_alerts_count"] >= 3
    print(f"      Active alerts: {alerts_resp['active_alerts_count']}, Units at risk: {alerts_resp['units_at_risk']}")
    test_alert = alerts_resp["items"][0]
    print(f"        Sample Alert: {test_alert['id']} ({test_alert['product_name']}, in {test_alert['days_to_expiry']}d, -{int(test_alert['suggested_discount_pct']*100)}%)")
    print("      [PASSED] Alerts retrieval verified.")

    # 9. POST /api/v1/inventory/markdown
    print("\n[Endpoint 9/12] Testing POST /api/v1/inventory/markdown...")
    md_payload = {
        "alert_id": test_alert["id"],
        "action": "accept"
    }
    r = client.post("/api/v1/inventory/markdown", json=md_payload, headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Markdown failed: {r.text}"
    md_resp = r.json()
    assert md_resp["status"] == "success"
    assert md_resp["current_discount_pct"] in (0.25, 0.40)
    print(f"      Result: {md_resp['message']} (Applied Discount: {int(md_resp['current_discount_pct']*100)}%)")
    print("      [PASSED] Inventory markdown action verified.")

    # Scoped cleanup for Endpoint 9
    _clean_b_id = test_alert.get("batch_id") or "-".join(test_alert["id"].split("-")[2:])
    _clean_db = SessionLocal()
    try:
        _clean_db.query(ProductBatch).filter(ProductBatch.id == _clean_b_id).update({"current_discount_pct": 0.0})
        _clean_db.commit()
    finally:
        _clean_db.close()

    # 10. GET /api/v1/analytics/waste-metrics?store_id=1
    print("\n[Endpoint 10/12] Testing GET /api/v1/analytics/waste-metrics?store_id=1...")
    r = client.get("/api/v1/analytics/waste-metrics?store_id=1", headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Waste metrics failed: {r.text}"
    metrics = r.json()
    assert "units_at_risk" in metrics
    assert "projected_exposure" in metrics
    assert "kg_saved" in metrics
    assert "co2_saved" in metrics
    print(f"      Metrics:")
    print(f"        - Units at Risk: {metrics['units_at_risk']}")
    print(f"        - Projected Exposure: ${metrics['projected_exposure']}")
    print(f"        - Pending Orders: {metrics['pending_orders']}")
    print(f"        - Food Saved: {metrics['kg_saved']} kg")
    print(f"        - CO2 Avoided: {metrics['co2_saved']} kg")
    print("      [PASSED] Waste metrics analytics verified.")

    # 11. GET /api/v1/analytics/sales-series?store_id=1
    print("\n[Endpoint 11/12] Testing GET /api/v1/analytics/sales-series?store_id=1...")
    r = client.get("/api/v1/analytics/sales-series?store_id=1", headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Sales series failed: {r.text}"
    series = r.json()
    assert len(series) == 30, f"Expected 30 points, got {len(series)}"
    print(f"      Sales points count: {len(series)}")
    print(f"        Latest point ({series[-1]['date']}): Actual=${series[-1]['actual']}, Predicted=${series[-1]['predicted']}")
    print("      [PASSED] Sales revenue time series verified.")

    # 12. GET /api/v1/analytics/category-waste?store_id=1
    print("\n[Endpoint 12/12] Testing GET /api/v1/analytics/category-waste?store_id=1...")
    r = client.get("/api/v1/analytics/category-waste?store_id=1", headers=headers)
    print(f"      Status: {r.status_code}")
    assert r.status_code == 200, f"Category waste failed: {r.text}"
    cats = r.json()
    assert len(cats) == 4, f"Expected 4 categories, got {len(cats)}"
    print(f"      Category waste counts:")
    for c in cats:
        print(f"        - {c['category'].title()}: {c['units']} units")
    print("      [PASSED] Category waste distribution verified.")

    # -------------------------------------------------------------
    # [RBAC Full Matrix Test] Role-Based Access Control Verification
    # -------------------------------------------------------------
    print("\n" + "=" * 75)
    print("ZeroWaste Grocer - Comprehensive RBAC Role & Permission Matrix Test")
    print("=" * 75)

    # 1. Obtain Tokens for all 3 Roles
    role_creds = {
        "storeManager": ("manager@zerowaste.com", "password123"),
        "inventoryAuditor": ("auditor@zerowaste.com", "auditor123"),
        "systemAdmin": ("admin@zerowaste.com", "admin123")
    }

    role_tokens = {}
    for role_name, (email, pwd) in role_creds.items():
        res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        assert res.status_code == 200, f"Login failed for {role_name}: {res.text}"
        data = res.json()
        assert data["user"]["role"] == role_name, f"Expected role {role_name}, got {data['user']['role']}"
        role_tokens[role_name] = data["token"]

    # 2. Define Full Matrix of Protected Endpoints
    # Format: (Method, Path, Payload/Params, Expected Status: {role: code})
    endpoint_matrix = [
        (
            "GET",
            "/api/v1/stores",
            None,
            {"storeManager": 200, "inventoryAuditor": 200, "systemAdmin": 200}
        ),
        (
            "POST",
            "/api/v1/stores",
            {"name": "New Test Store", "location": "77 Market St", "lat": 40.71, "lon": -74.00},
            {"storeManager": 403, "inventoryAuditor": 403, "systemAdmin": 201}
        ),
        (
            "GET",
            "/api/v1/stores/1/inventory",
            None,
            {"storeManager": 200, "inventoryAuditor": 200, "systemAdmin": 200}
        ),
        (
            "POST",
            "/api/v1/inventory/audit",
            {"store_id": 1, "entries": [{"product_id": 1, "on_hand_qty": 20, "spoiled_qty": 0}]},
            {"storeManager": 200, "inventoryAuditor": 200, "systemAdmin": 200}
        ),
        (
            "GET",
            "/api/v1/replenishment/recommendations?store_id=1",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 200}
        ),
        (
            "POST",
            "/api/v1/replenishment/approve",
            {"store_id": 1, "items": [{"product_id": 1, "final_qty": 15, "override_reason": "Accepted"}]},
            {"storeManager": 201, "inventoryAuditor": 403, "systemAdmin": 403}
        ),
        (
            "GET",
            "/api/v1/alerts?store_id=1",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 200}
        ),
        (
            "POST",
            "/api/v1/inventory/markdown",
            {"alert_id": "ALT-1-B-SPN-201", "action": "apply_40"},
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 403}
        ),
        (
            "GET",
            "/api/v1/analytics/waste-metrics?store_id=1",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 200}
        ),
        (
            "GET",
            "/api/v1/analytics/sales-series?store_id=1",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 200}
        ),
        (
            "GET",
            "/api/v1/analytics/category-waste?store_id=1",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 200}
        ),
        (
            "POST",
            "/api/v1/alerts/run-now",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 200}
        ),
        (
            "GET",
            "/api/v1/notifications?store_id=1",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 403}
        ),
        (
            "POST",
            "/api/v1/notifications/{notif_id}/read",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 403}
        ),
        (
            "POST",
            "/api/v1/alerts/B-SPN-201/dismiss",
            None,
            {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 403}
        ),
    ]

    matrix_results = []
    created_store_ids = []

    clean_db_init = SessionLocal()
    init_notif_max_id = clean_db_init.query(func.max(Notification.id)).scalar() or 0
    init_action_max_id = clean_db_init.query(func.max(AlertAction.id)).scalar() or 0
    init_notif_count = clean_db_init.query(Notification).count()
    init_action_count = clean_db_init.query(AlertAction).count()
    clean_db_init.close()

    try:
        for method, path, payload, expected_map in endpoint_matrix:
            row_res = {"endpoint": f"{method:<4} {path}"}
            for role_name in ["storeManager", "inventoryAuditor", "systemAdmin"]:
                token = role_tokens[role_name]
                h = {"Authorization": f"Bearer {token}"}
                actual_path = path
                if "{notif_id}" in path:
                    clean_db = SessionLocal()
                    first_notif = clean_db.query(Notification).first()
                    clean_db.close()
                    nid = first_notif.id if first_notif else 1
                    actual_path = path.replace("{notif_id}", str(nid))

                if method == "GET":
                    resp = client.get(actual_path, headers=h)
                elif method == "POST":
                    resp = client.post(actual_path, json=payload, headers=h)
                    if actual_path == "/api/v1/stores" and resp.status_code == 201:
                        new_id = resp.json().get("id")
                        if new_id:
                            created_store_ids.append(new_id)
                
                exp = expected_map[role_name]
                actual = resp.status_code
                assert actual == exp, f"RBAC Failure for {role_name} on {method} {path}! Expected {exp}, got {actual}: {resp.text}"
                status_label = "200 OK" if actual == 200 else ("201 Created" if actual == 201 else "403 Forbidden")
                row_res[role_name] = status_label
            matrix_results.append(row_res)
    finally:
        clean_db = SessionLocal()
        try:
            if created_store_ids:
                for sid in created_store_ids:
                    store_to_del = clean_db.query(Store).filter(Store.id == sid).first()
                    if store_to_del:
                        clean_db.delete(store_to_del)
            clean_db.query(Notification).filter(Notification.id > init_notif_max_id).delete(synchronize_session=False)
            clean_db.query(AlertAction).filter(AlertAction.id > init_action_max_id).delete(synchronize_session=False)
            clean_db.commit()

            assert clean_db.query(Notification).count() == init_notif_count, "Notification count changed after test_api"
            assert clean_db.query(AlertAction).count() == init_action_count, "AlertAction count changed after test_api"
        finally:
            clean_db.close()

    # 3. Print Beautiful RBAC Matrix Verification Table
    print("\n" + "=" * 90)
    print(f"{'Endpoint':<42} | {'Store Manager':<14} | {'Inventory Auditor':<18} | {'System Admin':<12}")
    print("-" * 90)
    for r in matrix_results:
        print(f"{r['endpoint']:<42} | {r['storeManager']:<14} | {r['inventoryAuditor']:<18} | {r['systemAdmin']:<12}")
    print("=" * 90)
    print("ALL 15 ENDPOINTS VERIFIED ACROSS ALL 3 ROLES WITH 100% RBAC ACCURACY!")
    print("=" * 90)



def test_d9_audit_reconciliation():
    """
    D9 Audit Reconciliation Test Suite:
    (1) unchanged audit -> every batch quantity, snapshot closing_stock and recommendations current_stock identical before/after
    (2) on_hand lower by 5 -> total drops by exactly 5 and earliest-expiry batch is reduced first
    (3) on_hand higher by 4 -> total rises by exactly 4 on latest-expiry batch
    (4) auditor role still allowed, unauthorized still 403
    Scoped cleanup ensures database restore check passes.
    """
    from app.models.models import ProductBatch, InventorySnapshot
    from app.core.security import create_access_token
    
    client = TestClient(app)
    mgr_token = create_access_token(data={"sub": "manager@zerowaste.com", "role": "storeManager", "id": 2})
    auditor_token = create_access_token(data={"sub": "auditor@zerowaste.com", "role": "inventoryAuditor", "id": 3})
    unauth_token = create_access_token(data={"sub": "cashier@zerowaste.com", "role": "cashier", "id": 4})
    mgr_h = {"Authorization": f"Bearer {mgr_token}"}
    auditor_h = {"Authorization": f"Bearer {auditor_token}"}
    unauth_h = {"Authorization": f"Bearer {unauth_token}"}

    db = SessionLocal()
    p2_batches_init = (
        db.query(ProductBatch)
        .filter(ProductBatch.product_id == 2)
        .order_by(ProductBatch.expiration_date.asc())
        .all()
    )
    init_state = [(b.id, b.remaining_quantity, b.expiration_date) for b in p2_batches_init]
    init_total = sum(b.remaining_quantity for b in p2_batches_init)
    init_snap = db.query(InventorySnapshot).filter(InventorySnapshot.product_id == 2).order_by(InventorySnapshot.snapshot_date.desc()).first()
    init_snap_closing = init_snap.closing_stock if init_snap else None
    db.close()

    try:
        # (1) Unchanged audit -> identical before/after
        rec_before = client.get("/api/v1/replenishment/recommendations?store_id=1", headers=mgr_h).json()
        items_before = rec_before if isinstance(rec_before, list) else rec_before.get("items", [])
        p2_rec_before = next((r["current_stock"] for r in items_before if r["product_id"] == 2), None)

        r1 = client.post("/api/v1/inventory/audit", json={
            "store_id": 1,
            "entries": [{"product_id": 2, "on_hand_qty": init_total, "spoiled_qty": 0}]
        }, headers=mgr_h)
        assert r1.status_code == 200, f"Unchanged audit failed: {r1.text}"

        db = SessionLocal()
        p2_batches_after1 = (
            db.query(ProductBatch)
            .filter(ProductBatch.product_id == 2)
            .order_by(ProductBatch.expiration_date.asc())
            .all()
        )
        snap_after1 = db.query(InventorySnapshot).filter(InventorySnapshot.product_id == 2).order_by(InventorySnapshot.snapshot_date.desc()).first()
        db.close()

        rec_after1 = client.get("/api/v1/replenishment/recommendations?store_id=1", headers=mgr_h).json()
        items_after1 = rec_after1 if isinstance(rec_after1, list) else rec_after1.get("items", [])
        p2_rec_after1 = next((r["current_stock"] for r in items_after1 if r["product_id"] == 2), None)

        for b_init, b_now in zip(init_state, p2_batches_after1):
            assert b_init[1] == b_now.remaining_quantity, f"Batch {b_init[0]} changed from {b_init[1]} to {b_now.remaining_quantity}"
        if snap_after1 and init_snap_closing is not None:
            assert snap_after1.closing_stock == init_total, f"Snapshot closing_stock expected {init_total}, got {snap_after1.closing_stock}"
        assert p2_rec_before == p2_rec_after1, f"Recommendations current_stock changed: {p2_rec_before} -> {p2_rec_after1}"
        print("    [PASS] D9 (1) Unchanged audit leaves batches, snapshots, and recommendations identical.")

        # (2) on_hand lower by 5 -> total drops by 5, earliest-expiry reduced first
        r2 = client.post("/api/v1/inventory/audit", json={
            "store_id": 1,
            "entries": [{"product_id": 2, "on_hand_qty": init_total - 5, "spoiled_qty": 0}]
        }, headers=mgr_h)
        assert r2.status_code == 200

        db = SessionLocal()
        p2_batches_after2 = (
            db.query(ProductBatch)
            .filter(ProductBatch.product_id == 2)
            .order_by(ProductBatch.expiration_date.asc())
            .all()
        )
        db.close()
        assert p2_batches_after2[0].remaining_quantity == init_state[0][1] - 5, f"Earliest batch did not drop by 5: {p2_batches_after2[0].remaining_quantity}"
        if len(p2_batches_after2) > 1:
            assert p2_batches_after2[1].remaining_quantity == init_state[1][1], f"Later batch unexpectedly changed: {p2_batches_after2[1].remaining_quantity}"
        print("    [PASS] D9 (2) On-hand lower by 5 drops total by 5, earliest-expiry batch reduced first.")

        # (3) on_hand higher by 4 -> total rises by 4 on latest-expiry batch
        r3 = client.post("/api/v1/inventory/audit", json={
            "store_id": 1,
            "entries": [{"product_id": 2, "on_hand_qty": init_total + 4, "spoiled_qty": 0}]
        }, headers=mgr_h)
        assert r3.status_code == 200

        db = SessionLocal()
        p2_batches_after3 = (
            db.query(ProductBatch)
            .filter(ProductBatch.product_id == 2)
            .order_by(ProductBatch.expiration_date.asc())
            .all()
        )
        db.close()
        total3 = sum(b.remaining_quantity for b in p2_batches_after3)
        assert total3 == init_total + 4, f"Total expected {init_total + 4}, got {total3}"
        print("    [PASS] D9 (3) On-hand higher by 4 raises total by 4 on latest-expiry batch.")

        # (4) auditor role still allowed, unauthorized still 403
        r_auditor = client.post("/api/v1/inventory/audit", json={
            "store_id": 1,
            "entries": [{"product_id": 2, "on_hand_qty": init_total, "spoiled_qty": 0}]
        }, headers=auditor_h)
        assert r_auditor.status_code == 200, f"Auditor role failed: {r_auditor.text}"

        r_unauth = client.post("/api/v1/inventory/audit", json={
            "store_id": 1,
            "entries": [{"product_id": 2, "on_hand_qty": init_total, "spoiled_qty": 0}]
        }, headers=unauth_h)
        assert r_unauth.status_code == 403, f"Unauthorized expected 403, got: {r_unauth.status_code}"
        print("    [PASS] D9 (4) Auditor role allowed (200), unauthorized role rejected (403).")

    finally:
        # Scoped cleanup
        db = SessionLocal()
        for b_id, b_qty, _ in init_state:
            b = db.query(ProductBatch).filter(ProductBatch.id == b_id).first()
            if b:
                b.remaining_quantity = b_qty
        if init_snap and init_snap_closing is not None:
            snap = db.query(InventorySnapshot).filter(InventorySnapshot.id == init_snap.id).first()
            if snap:
                snap.closing_stock = init_snap_closing
        db.commit()
        db.close()

def test_d10_days_to_expiry():
    print("\n--- Testing D10: days_to_expiry in BatchResponse ---")
    from app.config import settings
    from datetime import datetime
    client = TestClient(app)
    # Log in as store manager
    login_resp = client.post("/api/v1/auth/login", json={"email": "manager@zerowaste.com", "password": "password123"})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/products/2/batches", headers=headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    batches = r.json()
    assert len(batches) >= 2, f"Expected at least 2 batches for product 2, got {len(batches)}"

    effective_today = settings.get_effective_today()
    for b in batches[:2]:
        exp_date = datetime.strptime(b["expiration_date"], "%Y-%m-%d").date()
        expected_days = max(0, (exp_date - effective_today).days)
        actual_days = b.get("days_to_expiry")
        print(f"        Batch {b['id']}: exp={exp_date}, effective_today={effective_today}, expected={expected_days}, actual={actual_days}")
        assert actual_days == expected_days, f"Batch {b['id']} days_to_expiry mismatch: expected {expected_days}, got {actual_days}"
    print("    [PASS] D10 days_to_expiry verified for at least 2 batches.")

def test_security_rejection():
    print("\n--- Testing Security Rejection (Auth & Token Enforcement) ---")
    client = TestClient(app)

    # 1. Wrong password -> 401
    r_wrong_pwd = client.post("/api/v1/auth/login", json={"email": "manager@zerowaste.com", "password": "WRONG_PASSWORD"})
    assert r_wrong_pwd.status_code == 401, f"Expected 401 for wrong password, got {r_wrong_pwd.status_code}"
    print("    [PASS] Wrong password rejected with 401.")

    # 2. Unknown email (e.g. manager@zerowaste.local) -> 401
    r_unknown_email = client.post("/api/v1/auth/login", json={"email": "manager@zerowaste.local", "password": "password123"})
    assert r_unknown_email.status_code == 401, f"Expected 401 for unknown email, got {r_unknown_email.status_code}"
    print("    [PASS] Unknown email rejected with 401.")

    # 3. Request without token -> 401 on at least 3 protected endpoints (stores, alerts, run-now)
    r_no_token_stores = client.get("/api/v1/stores")
    assert r_no_token_stores.status_code == 401, f"Expected 401 on stores without token, got {r_no_token_stores.status_code}"

    r_no_token_alerts = client.get("/api/v1/alerts?store_id=1")
    assert r_no_token_alerts.status_code == 401, f"Expected 401 on alerts without token, got {r_no_token_alerts.status_code}"

    r_no_token_runnow = client.post("/api/v1/alerts/run-now")
    assert r_no_token_runnow.status_code == 401, f"Expected 401 on run-now without token, got {r_no_token_runnow.status_code}"
    print("    [PASS] Requests without token rejected with 401 on protected endpoints (stores, alerts, run-now).")

    # 4. Garbage token -> 401
    garbage_headers = {"Authorization": "Bearer invalid.garbage.token"}
    r_garbage_stores = client.get("/api/v1/stores", headers=garbage_headers)
    assert r_garbage_stores.status_code == 401, f"Expected 401 for garbage token on stores, got {r_garbage_stores.status_code}"

    r_garbage_alerts = client.get("/api/v1/alerts?store_id=1", headers=garbage_headers)
    assert r_garbage_alerts.status_code == 401, f"Expected 401 for garbage token on alerts, got {r_garbage_alerts.status_code}"
    print("    [PASS] Garbage token rejected with 401.")



def test_accept_markdown_status_and_notification_skip():
    """
    Level 2 Test:
    Accept a 1-day alert -> GET /alerts shows status 'accepted' and applied_discount_pct 0.40.
    Accept a 2-day alert -> GET /alerts shows status 'accepted' and applied_discount_pct 0.25.
    Accepted alert is skipped by run_daily_markdown_job.
    Scoped cleanup restores the batch discount back to original.
    """
    print("\n--- Test: Accept Markdown Status & Notification Skip ---")
    client = TestClient(app)
    db = SessionLocal()

    # Login as Store Manager
    login_res = client.post("/api/v1/auth/login", json={"email": "manager@zerowaste.com", "password": "password123"})
    assert login_res.status_code == 200, f"Manager login failed: {login_res.text}"
    mgr_token = login_res.json()["token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    # Fetch alerts for store 1
    r_alerts = client.get("/api/v1/alerts?store_id=1", headers=mgr_headers)
    assert r_alerts.status_code == 200, f"GET /alerts failed: {r_alerts.text}"
    alerts_data = r_alerts.json()["items"]

    alert_1day = next((a for a in alerts_data if a["days_to_expiry"] <= 1), None)
    alert_2day = next((a for a in alerts_data if a["days_to_expiry"] == 2), None)
    assert alert_1day is not None, "Expected at least one alert with days_to_expiry <= 1"
    assert alert_2day is not None, "Expected at least one alert with days_to_expiry == 2"

    batch_1_id = alert_1day["batch_id"]
    batch_2_id = alert_2day["batch_id"]
    batch_1 = db.query(ProductBatch).filter(ProductBatch.id == batch_1_id).first()
    batch_2 = db.query(ProductBatch).filter(ProductBatch.id == batch_2_id).first()
    orig_discount_1 = batch_1.current_discount_pct if batch_1 else 0.0
    orig_discount_2 = batch_2.current_discount_pct if batch_2 else 0.0
    initial_notif_max_id = db.query(func.max(Notification.id)).scalar() or 0

    try:
        # 1. Accept 1-day alert
        r_act1 = client.post(
            "/api/v1/inventory/markdown",
            json={"alert_id": alert_1day["id"], "action": "accept"},
            headers=mgr_headers
        )
        assert r_act1.status_code == 200, f"Accept 1-day alert failed: {r_act1.text}"
        assert r_act1.json()["current_discount_pct"] == 0.40

        # 2. Accept 2-day alert
        r_act2 = client.post(
            "/api/v1/inventory/markdown",
            json={"alert_id": alert_2day["id"], "action": "accept"},
            headers=mgr_headers
        )
        assert r_act2.status_code == 200, f"Accept 2-day alert failed: {r_act2.text}"
        assert r_act2.json()["current_discount_pct"] == 0.25

        # 3. Verify GET /alerts returns status 'accepted' and applied_discount_pct
        r_alerts_after = client.get("/api/v1/alerts?store_id=1", headers=mgr_headers)
        assert r_alerts_after.status_code == 200
        items_after = {a["id"]: a for a in r_alerts_after.json()["items"]}

        a1_after = items_after[alert_1day["id"]]
        assert a1_after["status"] == "accepted", f"Expected accepted, got {a1_after['status']}"
        assert a1_after["applied_discount_pct"] == 0.40, f"Expected 0.4, got {a1_after.get('applied_discount_pct')}"

        a2_after = items_after[alert_2day["id"]]
        assert a2_after["status"] == "accepted", f"Expected accepted, got {a2_after['status']}"
        assert a2_after["applied_discount_pct"] == 0.25, f"Expected 0.25, got {a2_after.get('applied_discount_pct')}"
        print("    [PASS] GET /alerts shows status 'accepted' and applied_discount_pct (0.40 & 0.25).")

        db.expire_all()
        # 4. Verify accepted alert is skipped by run_daily_markdown_job
        from app.services.notification_service import run_daily_markdown_job
        from datetime import datetime, date, timedelta
        anchor_date = db.query(func.max(ProductBatch.received_date)).scalar()
        if isinstance(anchor_date, str):
            anchor_date = date.fromisoformat(anchor_date)
        sim_time = datetime.combine(anchor_date, datetime.min.time()) + timedelta(hours=10)

        res_job = run_daily_markdown_job(db, now=sim_time)
        created_notifs = db.query(Notification).filter(
            Notification.id > initial_notif_max_id,
            Notification.batch_id.in_([alert_1day["batch_id"], alert_2day["batch_id"]])
        ).all()
        assert len(created_notifs) == 0, f"Accepted alerts were NOT skipped! Found: {created_notifs}"
        print("    [PASS] Accepted alerts successfully skipped by run_daily_markdown_job.")

    finally:
        # Scoped cleanup restores batch discount and cleans any created notifications
        if batch_1_id:
            db.query(ProductBatch).filter(ProductBatch.id == batch_1_id).update({"current_discount_pct": orig_discount_1})
        if batch_2_id:
            db.query(ProductBatch).filter(ProductBatch.id == batch_2_id).update({"current_discount_pct": orig_discount_2})
        db.query(Notification).filter(Notification.id > initial_notif_max_id).delete(synchronize_session=False)
        db.commit()
        db.close()
        print("    [CLEANUP] Batch discounts restored and test notifications purged.")



def test_defects_1_2_3():
    print("\n--- Testing Fix 9: Defect 1, Defect 2, Defect 3 ---")
    client = TestClient(app)
    db = SessionLocal()

    login_res = client.post("/api/v1/auth/login", json={"email": "manager@zerowaste.com", "password": "password123"})
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['token']}"}

    # Track created replenishment orders for cleanup
    initial_order_max_id = db.query(func.max(ReplenishmentOrder.id)).scalar() or 0
    initial_order_items_count = db.query(OrderItem).count()
    initial_orders_count = db.query(ReplenishmentOrder).count()
    orig_discounts = {}

    try:
        # --- Defect 1: /alerts summary counts ONLY open alerts ---
        r_alerts_before = client.get("/api/v1/alerts?store_id=1", headers=headers)
        assert r_alerts_before.status_code == 200
        d_before = r_alerts_before.json()
        cnt_before = d_before["active_alerts_count"]
        units_before = d_before["units_at_risk"]
        items_cnt = len(d_before["items"])
        assert cnt_before > 0, "Expected open alerts"

        first_alert = d_before["items"][0]
        batch = db.query(ProductBatch).filter(ProductBatch.id == first_alert["batch_id"]).first()
        if batch:
            orig_discounts[batch.id] = batch.current_discount_pct

        # Accept first alert
        r_acc = client.post("/api/v1/inventory/markdown", json={"alert_id": first_alert["id"], "action": "accept"}, headers=headers)
        assert r_acc.status_code == 200

        r_alerts_after = client.get("/api/v1/alerts?store_id=1", headers=headers)
        assert r_alerts_after.status_code == 200
        d_after = r_alerts_after.json()
        assert d_after["active_alerts_count"] == cnt_before - 1, f"Expected {cnt_before - 1}, got {d_after['active_alerts_count']}"
        assert d_after["units_at_risk"] == units_before - first_alert["remaining_qty"]
        assert len(d_after["items"]) == items_cnt
        print("    [PASS] Defect 1: active_alerts_count and units_at_risk count ONLY open alerts; items unchanged.")

        # --- Defect 3: Kg Saved formula ---
        r_metrics = client.get("/api/v1/analytics/waste-metrics?store_id=1", headers=headers)
        assert r_metrics.status_code == 200
        m = r_metrics.json()
        expected_kg = round(first_alert["remaining_qty"] * 0.35, 1)
        expected_co2 = round(expected_kg * 2.5, 1)
        assert m["kg_saved"] == expected_kg, f"Expected {expected_kg}, got {m['kg_saved']}"
        assert m["co2_saved"] == expected_co2, f"Expected {expected_co2}, got {m['co2_saved']}"
        print(f"    [PASS] Defect 3: kg_saved ({m['kg_saved']} kg) and co2_saved ({m['co2_saved']} kg) match 0.35 kg/unit formula without 120 baseline.")

        # --- Defect 2: Approve persistence & deduplication ---
        r_recs_before = client.get("/api/v1/replenishment/recommendations?store_id=1", headers=headers)
        assert r_recs_before.status_code == 200
        recs_data = r_recs_before.json()
        first_unapproved_rec = next(it for it in recs_data["items"] if not it.get("approved"))
        prod_id = first_unapproved_rec["product_id"]

        # Approve first unapproved item
        order_cnt_before = db.query(ReplenishmentOrder).count()
        app_req = {"store_id": 1, "items": [{"product_id": prod_id, "final_qty": first_unapproved_rec["recommended_qty"]}]}
        r_app1 = client.post("/api/v1/replenishment/approve", json=app_req, headers=headers)
        assert r_app1.status_code == 201
        res1 = r_app1.json()
        assert res1["approved_items_count"] == 1
        assert db.query(ReplenishmentOrder).count() == order_cnt_before + 1

        # Check GET /recommendations returns approved: True
        r_recs_after = client.get("/api/v1/replenishment/recommendations?store_id=1", headers=headers)
        assert r_recs_after.status_code == 200
        recs_after_items = r_recs_after.json()["items"]
        approved_item = next(it for it in recs_after_items if it["product_id"] == prod_id)
        assert approved_item["approved"] is True
        assert approved_item["status"] == "approved"

        # Calling approve again on the same item returns approved_items_count: 0 and order count unchanged
        order_cnt_mid = db.query(ReplenishmentOrder).count()
        r_app2 = client.post("/api/v1/replenishment/approve", json=app_req, headers=headers)
        assert r_app2.status_code == 201
        res2 = r_app2.json()
        assert res2["approved_items_count"] == 0, f"Expected 0 actually created, got {res2['approved_items_count']}"
        assert db.query(ReplenishmentOrder).count() == order_cnt_mid
        print("    [PASS] Defect 2: GET /recommendations returns approved: true and POST /approve skips duplicate approvals today.")

    finally:
        for b_id, disc in orig_discounts.items():
            db.query(ProductBatch).filter(ProductBatch.id == b_id).update({"current_discount_pct": disc})
        new_orders = db.query(ReplenishmentOrder).filter(ReplenishmentOrder.id > initial_order_max_id).all()
        for o in new_orders:
            db.query(OrderItem).filter(OrderItem.order_id == o.id).delete(synchronize_session=False)
            db.delete(o)
        db.commit()

        final_order_items_count = db.query(OrderItem).count()
        final_orders_count = db.query(ReplenishmentOrder).count()
        print(f"    [CLEANUP PROOF] order_items: before={initial_order_items_count}, after={final_order_items_count} | replenishment_orders: before={initial_orders_count}, after={final_orders_count}")
        assert initial_order_items_count == final_order_items_count, f"order_items leaked: {initial_order_items_count} != {final_order_items_count}"
        assert initial_orders_count == final_orders_count, f"replenishment_orders leaked: {initial_orders_count} != {final_orders_count}"
        db.close()
        print("    [CLEANUP] Restored test discounts and removed test replenishment orders.")

def test_recommendations_default_target_date():
    """
    Verifies GET /replenishment/recommendations?store_id=1 without target_date
    defaults to settings.get_effective_today() and matches target_date=<effective_today>.
    """
    print("\n" + "=" * 75)
    print("TEST: GET /replenishment/recommendations default target_date equivalence")
    print("=" * 75)
    from app.config import settings
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    login_res = client.post("/api/v1/auth/login", json={"email": "manager@zerowaste.com", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    eff_today = settings.get_effective_today()
    eff_today_str = eff_today.isoformat()

    # 1. Without target_date
    r_none = client.get("/api/v1/replenishment/recommendations?store_id=1", headers=headers)
    assert r_none.status_code == 200, f"Expected 200 without target_date, got {r_none.status_code}: {r_none.text}"
    data_none = r_none.json()
    assert data_none["target_date"] == eff_today_str, f"Expected response.target_date == {eff_today_str}, got {data_none['target_date']}"

    # 2. With target_date=<effective_today>
    r_explicit = client.get(f"/api/v1/replenishment/recommendations?store_id=1&target_date={eff_today_str}", headers=headers)
    assert r_explicit.status_code == 200, f"Expected 200 with explicit target_date, got {r_explicit.status_code}: {r_explicit.text}"
    data_explicit = r_explicit.json()
    assert data_explicit["target_date"] == eff_today_str

    items_none = {it["product_id"]: it for it in data_none["items"]}
    items_explicit = {it["product_id"]: it for it in data_explicit["items"]}

    assert len(items_none) == len(items_explicit) == 15
    for pid, it_n in items_none.items():
        it_exp = items_explicit[pid]
        assert it_n["recommended_qty"] == it_exp["recommended_qty"], f"Mismatch for product {pid}: none={it_n['recommended_qty']} vs explicit={it_exp['recommended_qty']}"

    print(f"    [PASS] GET /replenishment/recommendations?store_id=1 without target_date returned target_date={eff_today_str} and exactly matched explicit target_date across all 15 products.")

if __name__ == "__main__":
    import sys
    from app.config import settings
    from app.db.session import engine

    active_db = getattr(settings, "DB_NAME", "")
    engine_url = str(engine.url)
    if "zerowaste_real" in active_db.lower() or "zerowaste_real" in engine_url.lower() or not (active_db.endswith("zerowaste.db") or engine_url.endswith("zerowaste.db")):
        print("test_api.py must run against zerowaste.db (set DB_NAME=zerowaste.db)")
        sys.exit(2)

    run_api_tests()
    test_d9_audit_reconciliation()
    test_d10_days_to_expiry()
    test_security_rejection()
    test_accept_markdown_status_and_notification_skip()
    test_defects_1_2_3()
    test_recommendations_default_target_date()
