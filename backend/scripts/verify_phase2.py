import httpx
import json
import jwt

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_phase2():
    print("=== STARTING PHASE 2 VERIFICATION ===")
    
    # 1. Login with all 4 roles
    creds = {
        "clerk": ("clerk@zerowaste.com", "clerk123"),
        "auditor": ("auditor@zerowaste.com", "auditor123"),
        "manager": ("manager@zerowaste.com", "password123"),
        "admin": ("admin@zerowaste.com", "admin123")
    }
    
    tokens = {}
    users = {}
    
    for role, (email, pw) in creds.items():
        resp = httpx.post(f"{BASE_URL}/auth/login", json={"email": email, "password": pw})
        assert resp.status_code == 200, f"Login failed for {role}: {resp.text}"
        data = resp.json()
        tokens[role] = data.get("token") or data.get("access_token")
        users[role] = data["user"]
        
        # Decode token unverified just to inspect claims
        payload = jwt.decode(tokens[role], options={"verify_signature": False})
        print(f"Role '{role}' login OK: token role_id={payload.get('role_id')}, branch_id={payload.get('branch_id')}")
        
        # Verify UserResponse fields
        assert users[role]["role_id"] == role, f"Expected user role_id {role}, got {users[role].get('role_id')}"
        if role == "admin":
            assert users[role]["branch_id"] is None, "Admin branch_id should be None"
        else:
            assert users[role]["branch_id"] == 1, f"Expected branch_id 1, got {users[role].get('branch_id')}"

    print("\n--- Guardrail 1: POST /inventory/audit (auditor only, manager/clerk blocked) ---")
    audit_payload = {
        "store_id": 1,
        "entries": [
            {"product_id": 1, "on_hand_qty": 20, "spoiled_qty": 0}
        ]
    }
    
    # Auditor -> should succeed (200)
    r_auditor = httpx.post(f"{BASE_URL}/inventory/audit", json=audit_payload, headers={"Authorization": f"Bearer {tokens['auditor']}"})
    print(f"Auditor /inventory/audit status: {r_auditor.status_code} (Expected 200)")
    assert r_auditor.status_code == 200, r_auditor.text
    
    # Manager -> should be blocked (403)
    r_manager = httpx.post(f"{BASE_URL}/inventory/audit", json=audit_payload, headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager /inventory/audit status: {r_manager.status_code} (Expected 403)")
    assert r_manager.status_code == 403, f"Manager should be blocked from audit! Got {r_manager.status_code}"
    
    # Clerk -> should be blocked (403)
    r_clerk = httpx.post(f"{BASE_URL}/inventory/audit", json=audit_payload, headers={"Authorization": f"Bearer {tokens['clerk']}"})
    print(f"Clerk /inventory/audit status: {r_clerk.status_code} (Expected 403)")
    assert r_clerk.status_code == 403, f"Clerk should be blocked from audit! Got {r_clerk.status_code}"

    print("\n--- Guardrail 2: POST /reorders/approve and /replenishment/approve (manager only) ---")
    approve_payload = {
        "store_id": 1,
        "items": [
            {"product_id": 1, "final_qty": 10}
        ]
    }
    
    # Test both paths: /replenishment/approve and /reorders/approve
    for path in ["/replenishment/approve", "/reorders/approve"]:
        # Manager -> should succeed (201)
        r_mgr = httpx.post(f"{BASE_URL}{path}", json=approve_payload, headers={"Authorization": f"Bearer {tokens['manager']}"})
        print(f"Manager {path} status: {r_mgr.status_code} (Expected 201)")
        assert r_mgr.status_code in (200, 201), r_mgr.text
        
        # Auditor -> should be blocked (403)
        r_aud = httpx.post(f"{BASE_URL}{path}", json=approve_payload, headers={"Authorization": f"Bearer {tokens['auditor']}"})
        print(f"Auditor {path} status: {r_aud.status_code} (Expected 403)")
        assert r_aud.status_code == 403, f"Auditor should be blocked from approve! Got {r_aud.status_code}"
        
        # Clerk -> should be blocked (403)
        r_clk = httpx.post(f"{BASE_URL}{path}", json=approve_payload, headers={"Authorization": f"Bearer {tokens['clerk']}"})
        print(f"Clerk {path} status: {r_clk.status_code} (Expected 403)")
        assert r_clk.status_code == 403, f"Clerk should be blocked from approve! Got {r_clk.status_code}"

    print("\n--- Guardrail 3: Markdown / Alerts resolve endpoint (manager only) ---")
    # First get an alert or batch to resolve
    alerts_resp = httpx.get(f"{BASE_URL}/alerts?store_id=1", headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"GET /alerts status: {alerts_resp.status_code}")
    alerts_data = alerts_resp.json()
    alert_id = alerts_data["alerts"][0]["id"] if alerts_data.get("alerts") else "ALT-1-BATCH-TEST"
    
    markdown_payload = {
        "alert_id": alert_id,
        "action": "accept"
    }
    
    for path in ["/inventory/markdown", "/alerts/resolve"]:
        # Manager -> should succeed (200) or 404 if fake alert
        r_mgr = httpx.post(f"{BASE_URL}{path}", json=markdown_payload, headers={"Authorization": f"Bearer {tokens['manager']}"})
        print(f"Manager {path} status: {r_mgr.status_code} (Expected 200 or 404 if alert id mock)")
        assert r_mgr.status_code in (200, 404), r_mgr.text
        
        # Auditor -> should be 403
        r_aud = httpx.post(f"{BASE_URL}{path}", json=markdown_payload, headers={"Authorization": f"Bearer {tokens['auditor']}"})
        print(f"Auditor {path} status: {r_aud.status_code} (Expected 403)")
        assert r_aud.status_code == 403, f"Auditor should be blocked! Got {r_aud.status_code}"
        
        # Clerk -> should be 403
        r_clk = httpx.post(f"{BASE_URL}{path}", json=markdown_payload, headers={"Authorization": f"Bearer {tokens['clerk']}"})
        print(f"Clerk {path} status: {r_clk.status_code} (Expected 403)")
        assert r_clk.status_code == 403, f"Clerk should be blocked! Got {r_clk.status_code}"

    print("\n--- Branch Isolation: branch_id comes from JWT, cross-branch blocked ---")
    # Auditor in branch 1 tries to audit branch 999
    cross_audit = {"store_id": 999, "entries": [{"product_id": 1, "on_hand_qty": 10, "spoiled_qty": 0}]}
    r_cross = httpx.post(f"{BASE_URL}/inventory/audit", json=cross_audit, headers={"Authorization": f"Bearer {tokens['auditor']}"})
    print(f"Auditor audit store 999 status: {r_cross.status_code} (Expected 403)")
    assert r_cross.status_code == 403, "Cross branch audit should be 403"
    
    # Manager in branch 1 tries to approve order for branch 999
    cross_appr = {"store_id": 999, "items": [{"product_id": 1, "final_qty": 10}]}
    r_cross_appr = httpx.post(f"{BASE_URL}/replenishment/approve", json=cross_appr, headers={"Authorization": f"Bearer {tokens['manager']}"})
    print(f"Manager approve store 999 status: {r_cross_appr.status_code} (Expected 403)")
    assert r_cross_appr.status_code == 403, "Cross branch approve should be 403"

    print("\n--- Admin endpoints: admin has branch_id=None and can access branch 1 or all ---")
    r_admin_stores = httpx.get(f"{BASE_URL}/stores", headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin GET /stores status: {r_admin_stores.status_code} (Expected 200)")
    assert r_admin_stores.status_code == 200
    
    r_admin_inv = httpx.get(f"{BASE_URL}/stores/1/inventory", headers={"Authorization": f"Bearer {tokens['admin']}"})
    print(f"Admin GET /stores/1/inventory status: {r_admin_inv.status_code} (Expected 200)")
    assert r_admin_inv.status_code == 200

    print("\n>>> ALL PHASE 2 VERIFICATIONS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    test_phase2()
