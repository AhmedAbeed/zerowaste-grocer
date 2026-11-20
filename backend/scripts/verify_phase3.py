import httpx
import json
import uuid
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_phase3():
    print("=== STARTING PHASE 3 VERIFICATION ===")
    
    # Authenticate all 4 roles
    creds = {
        "clerk": ("clerk@zerowaste.com", "clerk123"),
        "auditor": ("auditor@zerowaste.com", "auditor123"),
        "manager": ("manager@zerowaste.com", "password123"),
        "admin": ("admin@zerowaste.com", "admin123")
    }
    
    tokens = {}
    for role, (email, pw) in creds.items():
        resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": email, "password": pw})
        assert resp.status_code == 200, f"Login failed for {role}: {resp.text}"
        tokens[role] = resp.json()["token"]

    future_date = (date.today() + timedelta(days=14)).isoformat()
    past_date = (date.today() - timedelta(days=2)).isoformat()
    unique_batch_id = f"BATCH-TEST-{uuid.uuid4().hex[:6].upper()}"

    # -------------------------------------------------------------
    # 1. POST /batches/incoming (clerk only, stock update in same tx, reject duplicates)
    # -------------------------------------------------------------
    print("\n--- 1. Testing POST /batches/incoming ---")
    valid_batch_payload = {
        "product_id": 1,
        "batch_id": unique_batch_id,
        "quantity": 25,
        "expiration_date": future_date
    }

    # Wrong role: manager -> 403
    r_mgr = httpx.post(f"{BASE_URL}/batches/incoming", json=valid_batch_payload, headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager /batches/incoming status: {r_mgr.status_code} (Expected 403)")
    assert r_mgr.status_code == 403, f"Manager should get 403, got {r_mgr.status_code}"

    # Wrong role: auditor -> 403
    r_aud = httpx.post(f"{BASE_URL}/batches/incoming", json=valid_batch_payload, headers={"Authorization": f"Bearer {tokens['auditor']}"})
    print(f"Auditor /batches/incoming status: {r_aud.status_code} (Expected 403)")
    assert r_aud.status_code == 403, f"Auditor should get 403, got {r_aud.status_code}"

    # Invalid: past expiration date -> 400
    past_batch = dict(valid_batch_payload, batch_id=f"PAST-{unique_batch_id}", expiration_date=past_date)
    r_past = httpx.post(f"{BASE_URL}/batches/incoming", json=past_batch, headers={"Authorization": f"Bearer {tokens['clerk']}"})
    print(f"Clerk past expiration date status: {r_past.status_code} (Expected 400)")
    assert r_past.status_code == 400, f"Past expiration date should fail with 400, got {r_past.status_code}"

    # Right role: clerk -> 201 Created
    r_clerk = httpx.post(f"{BASE_URL}/batches/incoming", json=valid_batch_payload, headers={"Authorization": f"Bearer {tokens['clerk']}"})
    print(f"Clerk valid /batches/incoming status: {r_clerk.status_code} (Expected 201)")
    assert r_clerk.status_code == 201, f"Clerk failed: {r_clerk.text}"
    batch_res = r_clerk.json()
    assert batch_res["status"] == "success"
    assert batch_res["batch_id"] == unique_batch_id
    print(f"  Created batch: {batch_res['batch_id']}, current_stock: {batch_res['current_stock']}")

    # Duplicate batch_id in same branch -> 409 Conflict
    r_dup = httpx.post(f"{BASE_URL}/batches/incoming", json=valid_batch_payload, headers={"Authorization": f"Bearer {tokens['clerk']}"})
    print(f"Clerk duplicate batch_id status: {r_dup.status_code} (Expected 409)")
    assert r_dup.status_code == 409, f"Duplicate batch should be 409, got {r_dup.status_code}"

    # -------------------------------------------------------------
    # 2. Admin endpoints (admin only)
    # -------------------------------------------------------------
    print("\n--- 2. Testing Admin Endpoints ---")
    
    # GET /admin/branches
    r_admin_b = httpx.get(f"{BASE_URL}/admin/branches", headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin GET /admin/branches status: {r_admin_b.status_code} (Expected 200)")
    assert r_admin_b.status_code == 200
    branches = r_admin_b.json()
    print(f"  Branches found: {len(branches)}")
    
    r_mgr_b = httpx.get(f"{BASE_URL}/admin/branches", headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager GET /admin/branches status: {r_mgr_b.status_code} (Expected 403)")
    assert r_mgr_b.status_code == 403

    # POST /admin/branches
    new_branch_payload = {
        "name": f"Eastside Hub {uuid.uuid4().hex[:4]}",
        "location": "Sector 9 Metro",
        "lat": 30.05,
        "lon": 31.25
    }
    r_create_b = httpx.post(f"{BASE_URL}/admin/branches", json=new_branch_payload, headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin POST /admin/branches status: {r_create_b.status_code} (Expected 201)")
    assert r_create_b.status_code == 201
    created_branch = r_create_b.json()
    print(f"  Created branch ID: {created_branch['id']}, Name: {created_branch['name']}")

    r_mgr_create_b = httpx.post(f"{BASE_URL}/admin/branches", json=new_branch_payload, headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager POST /admin/branches status: {r_mgr_create_b.status_code} (Expected 403)")
    assert r_mgr_create_b.status_code == 403

    # GET /admin/analytics/global
    r_admin_g = httpx.get(f"{BASE_URL}/admin/analytics/global", headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin GET /admin/analytics/global status: {r_admin_g.status_code} (Expected 200)")
    assert r_admin_g.status_code == 200
    global_data = r_admin_g.json()
    print(f"  Global analytics: {global_data['total_stores']} stores, {global_data['total_products']} products, stock={global_data['total_active_stock']}")

    r_mgr_g = httpx.get(f"{BASE_URL}/admin/analytics/global", headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager GET /admin/analytics/global status: {r_mgr_g.status_code} (Expected 403)")
    assert r_mgr_g.status_code == 403

    # -------------------------------------------------------------
    # 3. Broadcast system (POST /admin/broadcast, GET /broadcasts)
    # -------------------------------------------------------------
    print("\n--- 3. Testing Broadcast System ---")
    broadcast_payload = {
        "title": "Emergency Cold Storage Maintenance",
        "message": "Routine cooler inspection scheduled for tonight at 22:00.",
        "target_store_id": 1,
        "priority": "urgent"
    }

    # Wrong role: manager POST broadcast -> 403
    r_mgr_bc = httpx.post(f"{BASE_URL}/admin/broadcast", json=broadcast_payload, headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager POST /admin/broadcast status: {r_mgr_bc.status_code} (Expected 403)")
    assert r_mgr_bc.status_code == 403

    # Admin POST broadcast -> 201
    r_admin_bc = httpx.post(f"{BASE_URL}/admin/broadcast", json=broadcast_payload, headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin POST /admin/broadcast status: {r_admin_bc.status_code} (Expected 201)")
    assert r_admin_bc.status_code == 201
    bc_data = r_admin_bc.json()
    print(f"  Broadcast created ID: {bc_data['id']}, title: {bc_data['title']}")

    # Manager GET /broadcasts -> 200
    r_mgr_get_bc = httpx.get(f"{BASE_URL}/broadcasts", headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager GET /broadcasts status: {r_mgr_get_bc.status_code} (Expected 200)")
    assert r_mgr_get_bc.status_code == 200
    mgr_broadcasts = r_mgr_get_bc.json()
    assert len(mgr_broadcasts) >= 1
    print(f"  Manager received {len(mgr_broadcasts)} broadcast(s)")

    # -------------------------------------------------------------
    # 4. AI endpoints under /ai/ultra (/forecast, /recommendations, /feedback)
    # -------------------------------------------------------------
    print("\n--- 4. Testing AI Ultra Endpoints ---")
    
    # 4a. POST /ai/ultra/forecast
    # Admin without store_id -> MUST return 400 Bad Request
    r_admin_no_store = httpx.post(f"{BASE_URL}/ai/ultra/forecast", json={"product_id": 1}, headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin /ai/ultra/forecast without store_id status: {r_admin_no_store.status_code} (Expected 400)")
    assert r_admin_no_store.status_code == 400, f"Expected 400 when admin omits store_id, got {r_admin_no_store.status_code}"

    # Admin with store_id=1 -> 200
    r_admin_fc = httpx.post(f"{BASE_URL}/ai/ultra/forecast", json={"product_id": 1, "store_id": 1}, headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin /ai/ultra/forecast with store_id=1 status: {r_admin_fc.status_code} (Expected 200)")
    assert r_admin_fc.status_code == 200
    fc_data = r_admin_fc.json()
    print(f"  Forecast: product '{fc_data['product_name']}', predicted_demand={fc_data['predicted_demand']}, recommended_order={fc_data['recommended_order_units']}")

    # Manager -> 200 (branch_id inferred from JWT)
    r_mgr_fc = httpx.post(f"{BASE_URL}/ai/ultra/forecast", json={"product_id": 1}, headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager /ai/ultra/forecast status: {r_mgr_fc.status_code} (Expected 200)")
    assert r_mgr_fc.status_code == 200

    # Clerk & Auditor -> 403 Forbidden
    r_clk_fc = httpx.post(f"{BASE_URL}/ai/ultra/forecast", json={"product_id": 1}, headers={"Authorization": f"Bearer {tokens['clerk']}"})
    print(f"Clerk /ai/ultra/forecast status: {r_clk_fc.status_code} (Expected 403)")
    assert r_clk_fc.status_code == 403

    r_aud_fc = httpx.post(f"{BASE_URL}/ai/ultra/forecast", json={"product_id": 1}, headers={"Authorization": f"Bearer {tokens['auditor']}"})
    print(f"Auditor /ai/ultra/forecast status: {r_aud_fc.status_code} (Expected 403)")
    assert r_aud_fc.status_code == 403

    # 4b. GET /ai/ultra/recommendations
    # Admin without store_id -> MUST return 400 Bad Request
    r_admin_no_st_rec = httpx.get(f"{BASE_URL}/ai/ultra/recommendations", headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin /ai/ultra/recommendations without store_id status: {r_admin_no_st_rec.status_code} (Expected 400)")
    assert r_admin_no_st_rec.status_code == 400

    # Manager -> 200
    r_mgr_rec = httpx.get(f"{BASE_URL}/ai/ultra/recommendations", headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager /ai/ultra/recommendations status: {r_mgr_rec.status_code} (Expected 200)")
    assert r_mgr_rec.status_code == 200
    ultra_recs = r_mgr_rec.json()
    print(f"  Ultra recommendations count: {ultra_recs['total_items']}")

    # Clerk & Auditor -> 403
    r_clk_rec = httpx.get(f"{BASE_URL}/ai/ultra/recommendations", headers={"Authorization": f"Bearer {tokens['clerk']}"})
    print(f"Clerk /ai/ultra/recommendations status: {r_clk_rec.status_code} (Expected 403)")
    assert r_clk_rec.status_code == 403

    # 4c. POST /ai/ultra/feedback
    # Admin without store_id -> 400
    fb_payload = {
        "product_id": 1,
        "predicted_demand": 50.0,
        "actual_demand": 42.0,
        "spoiled_units": 3,
        "notes": "Weather turned colder than expected"
    }
    r_admin_no_st_fb = httpx.post(f"{BASE_URL}/ai/ultra/feedback", json=fb_payload, headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin /ai/ultra/feedback without store_id status: {r_admin_no_st_fb.status_code} (Expected 400)")
    assert r_admin_no_st_fb.status_code == 400

    # Auditor -> 201 Created
    r_aud_fb = httpx.post(f"{BASE_URL}/ai/ultra/feedback", json=fb_payload, headers={"Authorization": f"Bearer {tokens['auditor']}"})
    print(f"Auditor /ai/ultra/feedback status: {r_aud_fb.status_code} (Expected 201)")
    assert r_aud_fb.status_code == 201

    # Clerk -> 403
    r_clk_fb = httpx.post(f"{BASE_URL}/ai/ultra/feedback", json=fb_payload, headers={"Authorization": f"Bearer {tokens['clerk']}"})
    print(f"Clerk /ai/ultra/feedback status: {r_clk_fb.status_code} (Expected 403)")
    assert r_clk_fb.status_code == 403

    # -------------------------------------------------------------
    # 5. Keep legacy /replenishment/recommendations working
    # -------------------------------------------------------------
    print("\n--- 5. Testing Legacy /replenishment/recommendations ---")
    r_legacy = httpx.get(f"{BASE_URL}/replenishment/recommendations?store_id=1", headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Legacy /replenishment/recommendations status: {r_legacy.status_code} (Expected 200)")
    assert r_legacy.status_code == 200
    legacy_data = r_legacy.json()
    assert legacy_data["total_items"] > 0
    print(f"  Legacy items count: {legacy_data['total_items']}")

    print("\n>>> ALL PHASE 3 VERIFICATIONS PASSED PERFECTLY! <<<")

if __name__ == "__main__":
    test_phase3()
