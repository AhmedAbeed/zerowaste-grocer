"""
test_config_scale.py
Level 6 Part 1: Verification of DEMAND_SCALE configuration and overridability.
"""
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import settings, DEMAND_SCALE
from fastapi.testclient import TestClient
from main import app

BEFORE_RECOMMENDATIONS_SHA256 = "9729d493d31c82502813d8d1aaae06c72abbbb2ad0ef8ae41ace1e9ca3d78013"

def test_default_demand_scale():
    print("[1/4] Testing default DEMAND_SCALE in settings...")
    assert settings.DEMAND_SCALE == 250.0, f"Expected 250.0, got {settings.DEMAND_SCALE}"
    assert DEMAND_SCALE == 250.0, f"Expected module alias 250.0, got {DEMAND_SCALE}"
    print("      [PASSED] settings.DEMAND_SCALE == 250.0 by default.")

def test_env_override_demand_scale():
    print("\n[2/4] Testing DEMAND_SCALE override via environment variable in subprocess...")
    env = os.environ.copy()
    env["DEMAND_SCALE"] = "100"
    
    code = "from app.config import settings, DEMAND_SCALE; print(f'{settings.DEMAND_SCALE},{DEMAND_SCALE}')"
    res = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR)
    )
    assert res.returncode == 0, f"Subprocess failed: {res.stderr}"
    out = res.stdout.strip()
    s_val, a_val = out.split(",")
    assert float(s_val) == 100.0, f"Expected 100.0, got {s_val}"
    assert float(a_val) == 100.0, f"Expected alias 100.0, got {a_val}"
    print(f"      [PASSED] Subprocess settings.DEMAND_SCALE == 100.0 (output: {out})")

def test_recommendations_snapshot_parity():
    print("\n[3/4] Testing recommendations response sha256 parity with BEFORE snapshot...")
    client = TestClient(app)
    login_res = client.post("/api/v1/auth/login", json={"email": "manager@zerowaste.com", "password": "password123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/replenishment/recommendations?store_id=1", headers=headers)
    assert r.status_code == 200, f"Recommendations failed: {r.text}"
    json_sha = hashlib.sha256(r.text.encode("utf-8")).hexdigest()
    
    assert json_sha == BEFORE_RECOMMENDATIONS_SHA256, (
        f"SHA256 mismatch! Got {json_sha}, expected {BEFORE_RECOMMENDATIONS_SHA256}"
    )
    print(f"      [PASSED] Recommendations SHA256 identical to BEFORE snapshot: {json_sha}")

def test_demand_scale_impact_on_recommended_qty():
    print("\n[4/4] Testing impact of DEMAND_SCALE=100 on recommended_qty in subprocess...")
    code = """
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
login_res = client.post('/api/v1/auth/login', json={'email': 'manager@zerowaste.com', 'password': 'password123'})
token = login_res.json()['token']
headers = {'Authorization': f'Bearer {token}'}
r = client.get('/api/v1/replenishment/recommendations?store_id=1', headers=headers)
print(r.text)
"""
    # 1. Default run
    res_def = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR)
    )
    assert res_def.returncode == 0, f"Default run failed: {res_def.stderr}"
    data_def = json.loads([l for l in res_def.stdout.strip().splitlines() if l.startswith("{") or l.startswith("[")][-1])

    # 2. Scale 100 run
    env = os.environ.copy()
    env["DEMAND_SCALE"] = "100"
    res_100 = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR)
    )
    assert res_100.returncode == 0, f"Scale 100 run failed: {res_100.stderr}"
    data_100 = json.loads([l for l in res_100.stdout.strip().splitlines() if l.startswith("{") or l.startswith("[")][-1])

    diffs = []
    for it_def, it_100 in zip(data_def["items"], data_100["items"]):
        if it_def["recommended_qty"] != it_100["recommended_qty"]:
            diffs.append((it_def["product_name"], it_def["recommended_qty"], it_100["recommended_qty"]))

    assert len(diffs) > 0, "Expected recommended_qty of at least one product to differ when DEMAND_SCALE=100"
    print(f"      [PASSED] Differences confirmed in {len(diffs)} / {len(data_def['items'])} items (Sample: {diffs[0][0]} {diffs[0][1]} -> {diffs[0][2]})")

if __name__ == "__main__":
    print("=" * 70)
    print("ZeroWaste Grocer - DEMAND_SCALE Config & Override Test Suite")
    print("=" * 70)
    test_default_demand_scale()
    test_env_override_demand_scale()
    test_recommendations_snapshot_parity()
    test_demand_scale_impact_on_recommended_qty()
    print("\n" + "=" * 70)
    print("ALL DEMAND_SCALE CONFIG TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
