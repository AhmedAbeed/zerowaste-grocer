"""
test_notifications.py
Level 3 Automated Test Suite: Spoilage Markdown Notifications, Scheduler Wiring,
and Alert Dismiss Risk Audit Log Verification.
"""
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from main import app, create_markdown_scheduler
from app.db.session import SessionLocal
from sqlalchemy import func
from app.models.models import Notification, AlertAction, ProductBatch, Store
from app.services.alert_service import evaluate_store_spoilage_alerts
from app.services.notification_service import (
    run_daily_markdown_job,
    is_batch_dismissed,
    dismiss_batch
)
from app.config import settings

def run_tests():
    print("=" * 75)
    print("ZeroWaste Grocer - Level 3 Notifications & Scheduler Test Suite")
    print("=" * 75)

    client = TestClient(app)
    db = SessionLocal()

    # Track created IDs for strict cleanup
    created_notification_ids = set()
    created_alert_action_ids = set()

    try:
        # Record pre-test baseline max id and counts
        initial_notif_max_id = db.query(func.max(Notification.id)).scalar() or 0
        initial_action_max_id = db.query(func.max(AlertAction.id)).scalar() or 0
        initial_notif_count = db.query(Notification).count()
        initial_action_count = db.query(AlertAction).count()

        # -------------------------------------------------------------
        # T1: Job creates notifications
        # -------------------------------------------------------------
        print("\n[Test 1/7] Testing run_daily_markdown_job creation...")
        # Derive simulation time dynamically from the active batch dates under test
        anchor_date = db.query(func.max(ProductBatch.received_date)).scalar()
        if isinstance(anchor_date, str):
            anchor_date = date.fromisoformat(anchor_date)
        elif anchor_date is None:
            min_exp = db.query(func.min(ProductBatch.expiration_date)).filter(ProductBatch.remaining_quantity > 0).scalar()
            anchor_date = (min_exp - timedelta(days=1)) if min_exp else date.today()
        sim_time = datetime.combine(anchor_date, datetime.min.time()) + timedelta(hours=10)
        res_t1 = run_daily_markdown_job(db, now=sim_time)
        print(f"      Result: {res_t1}")
        assert res_t1["stores_processed"] == 3, f"Expected 3 stores, got {res_t1['stores_processed']}"
        assert res_t1["alerts_found"] > 0, "Expected at least 1 alert found"
        assert res_t1["notifications_created"] > 0, "Expected notifications created"
        assert res_t1["notifications_created"] == (
            res_t1["alerts_found"] - res_t1["skipped_dismissed"] - res_t1["skipped_duplicates"]
        )

        current_notif_count = db.query(Notification).count()
        assert current_notif_count >= res_t1["notifications_created"]
        print("      [PASSED] T1: Markdown job creates expected notifications successfully.")

        # -------------------------------------------------------------
        # T2: De-duplication on same alert_date
        # -------------------------------------------------------------
        print("\n[Test 2/7] Testing notification de-duplication...")
        res_t2 = run_daily_markdown_job(db, now=sim_time)
        print(f"      Result: {res_t2}")
        assert res_t2["notifications_created"] == 0, "Duplicate notifications were created!"
        assert res_t2["skipped_duplicates"] == res_t2["alerts_found"], (
            f"Expected {res_t2['alerts_found']} duplicates, got {res_t2['skipped_duplicates']}"
        )
        print("      [PASSED] T2: De-duplication verified (0 created, all flagged as duplicates).")

        # -------------------------------------------------------------
        # T3: GET /notifications as manager for store 1
        # -------------------------------------------------------------
        print("\n[Test 3/7] Testing GET /notifications as storeManager...")
        # Authenticate manager
        login_res = client.post("/api/v1/auth/login", json={"email": "manager@zerowaste.com", "password": "password123"})
        assert login_res.status_code == 200, f"Manager login failed: {login_res.text}"
        mgr_token = login_res.json()["token"]
        mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

        r3 = client.get("/api/v1/notifications?store_id=1", headers=mgr_headers)
        assert r3.status_code == 200, f"GET /notifications failed: {r3.text}"
        data3 = r3.json()
        items3 = data3["items"]
        unread3 = data3["unread_count"]
        assert len(items3) > 0, "Expected items in notification list"

        # Verify sorted newest first (created_at desc, id desc)
        for i in range(len(items3) - 1):
            assert items3[i]["created_at"] >= items3[i+1]["created_at"]
            if items3[i]["created_at"] == items3[i+1]["created_at"]:
                assert items3[i]["id"] >= items3[i+1]["id"]

        actual_unread_db = db.query(Notification).filter(Notification.store_id == 1, Notification.is_read == False).count()
        assert unread3 == actual_unread_db, f"Unread count mismatch: {unread3} vs {actual_unread_db}"

        # unread_only=true
        r3_unread = client.get("/api/v1/notifications?store_id=1&unread_only=true", headers=mgr_headers)
        assert r3_unread.status_code == 200
        for item in r3_unread.json()["items"]:
            assert item["is_read"] is False, "Found read item when unread_only=true"

        # limit=1
        r3_limit = client.get("/api/v1/notifications?store_id=1&limit=1", headers=mgr_headers)
        assert r3_limit.status_code == 200
        assert len(r3_limit.json()["items"]) == 1
        assert r3_limit.json()["unread_count"] == actual_unread_db
        print(f"      Store 1 unread count: {unread3}, retrieved items: {len(items3)}")
        print("      [PASSED] T3: Notification retrieval, sorting, unread_only, and limit verified.")

        # -------------------------------------------------------------
        # T4: POST /notifications/{id}/read
        # -------------------------------------------------------------
        print("\n[Test 4/7] Testing POST /notifications/{id}/read...")
        target_notif = db.query(Notification).filter(Notification.store_id == 1, Notification.is_read == False).first()
        assert target_notif is not None, "No unread notification found for test"

        r4 = client.post(f"/api/v1/notifications/{target_notif.id}/read", headers=mgr_headers)
        assert r4.status_code == 200, f"Mark read failed: {r4.text}"
        resp4 = r4.json()
        assert resp4["id"] == target_notif.id
        assert resp4["is_read"] is True

        # Verify unread count decreased by 1
        r4_check = client.get("/api/v1/notifications?store_id=1", headers=mgr_headers)
        assert r4_check.json()["unread_count"] == actual_unread_db - 1

        # Unknown ID returns 404
        r4_404 = client.post("/api/v1/notifications/999999/read", headers=mgr_headers)
        assert r4_404.status_code == 404, f"Expected 404 for unknown ID, got {r4_404.status_code}"
        print("      [PASSED] T4: Mark read and 404 error response verified.")

        # -------------------------------------------------------------
        # T5: Dismiss Alert & 6-Hour Postponement Verification
        # -------------------------------------------------------------
        print("\n[Test 5/7] Testing POST /alerts/{batch_id}/dismiss & postponement...")
        alerts_r = client.get("/api/v1/alerts?store_id=1", headers=mgr_headers)
        assert alerts_r.status_code == 200
        alerts_list = alerts_r.json()["items"]
        assert len(alerts_list) > 0, "No alerts found to test dismiss"
        sample_alert = alerts_list[0]
        sample_batch_id = sample_alert.get("batch_id")
        if not sample_batch_id:
            sample_batch_id = "-".join(sample_alert["id"].split("-")[2:])

        dismiss_now = sim_time + timedelta(minutes=30)
        # Call endpoint
        r5 = client.post(f"/api/v1/alerts/{sample_batch_id}/dismiss", headers=mgr_headers)
        assert r5.status_code == 200, f"Dismiss failed: {r5.text}"
        d5 = r5.json()
        assert d5["batch_id"] == sample_batch_id
        assert d5["status"] == "postponed"
        until_dt = datetime.fromisoformat(d5["dismissed_until"])
        assert until_dt > datetime.now(), "dismissed_until must be in the future"

        # Verify GET /alerts?store_id=1 no longer contains that batch
        alerts_after = client.get("/api/v1/alerts?store_id=1", headers=mgr_headers).json()["items"]
        active_batch_ids = [a.get("batch_id") or "-".join(a["id"].split("-")[2:]) for a in alerts_after]
        assert sample_batch_id not in active_batch_ids, f"Dismissed batch {sample_batch_id} still present in GET /alerts!"

        # Running job with now = T + 1 hour skips the batch (skipped_dismissed >= 1)
        res_t5_1 = run_daily_markdown_job(db, now=sim_time + timedelta(hours=1))
        assert res_t5_1["skipped_dismissed"] >= 1, "Dismissed batch was not skipped!"

        # Running job with simulated time > 6 hours (e.g. 7 hours later) treats batch as no longer dismissed
        # Use an alert_date in future relative to until_dt to avoid duplicate collision
        sim_future = until_dt + timedelta(hours=1)
        res_t5_2 = run_daily_markdown_job(db, now=sim_future)
        # Check that this batch is NOT in skipped_dismissed for future date
        assert is_batch_dismissed(db, sample_batch_id, now=sim_future) is False

        # Unknown batch id -> 404
        r5_404 = client.post("/api/v1/alerts/non_existent_batch_xyz/dismiss", headers=mgr_headers)
        assert r5_404.status_code == 404, f"Expected 404 for unknown batch, got {r5_404.status_code}"
        print("      [PASSED] T5: Dismiss postponement, alert hiding, and resume behavior verified.")

        # -------------------------------------------------------------
        # T6: RBAC Role Matrix Verification
        # -------------------------------------------------------------
        print("\n[Test 6/7] Testing RBAC role matrix for Level 3 endpoints...")
        auditor_res = client.post("/api/v1/auth/login", json={"email": "auditor@zerowaste.com", "password": "auditor123"})
        admin_res = client.post("/api/v1/auth/login", json={"email": "admin@zerowaste.com", "password": "admin123"})
        assert auditor_res.status_code == 200
        assert admin_res.status_code == 200
        auditor_token = auditor_res.json()["token"]
        admin_token = admin_res.json()["token"]

        tokens = {
            "storeManager": mgr_token,
            "inventoryAuditor": auditor_token,
            "systemAdmin": admin_token
        }

        # First existing notification id for testing
        test_nid = db.query(Notification.id).first()[0]

        l3_matrix = [
            ("GET", "/api/v1/notifications?store_id=1", None, {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 403}),
            ("POST", f"/api/v1/notifications/{test_nid}/read", None, {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 403}),
            ("POST", "/api/v1/alerts/run-now", None, {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 200}),
            ("POST", f"/api/v1/alerts/{sample_batch_id}/dismiss", None, {"storeManager": 200, "inventoryAuditor": 403, "systemAdmin": 403})
        ]

        matrix_rows = []
        for method, path, payload, exp_map in l3_matrix:
            row = {"endpoint": f"{method:<4} {path}"}
            for role_name in ["storeManager", "inventoryAuditor", "systemAdmin"]:
                h = {"Authorization": f"Bearer {tokens[role_name]}"}
                if method == "GET":
                    resp = client.get(path, headers=h)
                else:
                    resp = client.post(path, json=payload, headers=h)
                
                exp_status = exp_map[role_name]
                assert resp.status_code == exp_status, (
                    f"RBAC failed for {role_name} on {method} {path}! Expected {exp_status}, got {resp.status_code}"
                )
                row[role_name] = f"{resp.status_code} {'OK' if resp.status_code == 200 else 'Forbidden'}"
            matrix_rows.append(row)

        print("\n" + "=" * 90)
        print(f"{'Endpoint':<45} | {'Store Manager':<14} | {'Inventory Auditor':<18} | {'System Admin':<12}")
        print("-" * 90)
        for r in matrix_rows:
            print(f"{r['endpoint']:<45} | {r['storeManager']:<14} | {r['inventoryAuditor']:<18} | {r['systemAdmin']:<12}")
        print("=" * 90)
        print("      [PASSED] T6: All 4 Level 3 endpoints verified across all 3 roles!")

        # -------------------------------------------------------------
        # T7: Scheduler wiring test (no real waiting)
        # -------------------------------------------------------------
        print("\n[Test 7/7] Testing BackgroundScheduler job configuration...")
        sched = create_markdown_scheduler()
        assert sched.running is False, "Scheduler should NOT be running in unit test"
        job = sched.get_job("daily_markdown_job")
        assert job is not None, "Job 'daily_markdown_job' not found in scheduler!"
        
        # Check hour and minute on trigger
        trigger = job.trigger
        hour_field = next(f for f in trigger.fields if f.name == 'hour')
        minute_field = next(f for f in trigger.fields if f.name == 'minute')
        assert str(hour_field) == str(settings.MARKDOWN_JOB_HOUR), f"Expected hour {settings.MARKDOWN_JOB_HOUR}, got {hour_field}"
        assert str(minute_field) == str(settings.MARKDOWN_JOB_MINUTE), f"Expected minute {settings.MARKDOWN_JOB_MINUTE}, got {minute_field}"
        print(f"      Job trigger configured for: {settings.MARKDOWN_JOB_HOUR:02d}:{settings.MARKDOWN_JOB_MINUTE:02d} local time")
        print("      [PASSED] T7: Scheduler job wiring and trigger verified.")

        # -------------------------------------------------------------
        # T8: run_daily_markdown_job WITHOUT now & monkeypatched get_effective_today
        # -------------------------------------------------------------
        print("\n[Test 8/8] Testing run_daily_markdown_job WITHOUT now with monkeypatched settings.get_effective_today...")
        # Purge notifications/actions from earlier tests so T8 evaluates a clean run for derived_date
        db.query(Notification).filter(Notification.id > initial_notif_max_id).delete(synchronize_session=False)
        db.query(AlertAction).filter(AlertAction.id > initial_action_max_id).delete(synchronize_session=False)
        db.commit()

        min_exp = db.query(func.min(ProductBatch.expiration_date)).filter(ProductBatch.remaining_quantity > 0).scalar()
        max_exp = db.query(func.max(ProductBatch.expiration_date)).filter(ProductBatch.remaining_quantity > 0).scalar()
        if isinstance(min_exp, str):
            min_exp = date.fromisoformat(min_exp)
        if isinstance(max_exp, str):
            max_exp = date.fromisoformat(max_exp)

        # Derive a date (in real DB: 3 years in the past relative to date.today(); in synth DB: min_exp - 1d)
        derived_date = min_exp - timedelta(days=1)
        print(f"      Derivation: min_exp={min_exp}, max_exp={max_exp} -> derived effective_today={derived_date} (batches expire within 1-2 days)")

        orig_fn = settings.get_effective_today
        settings.get_effective_today = lambda: derived_date
        try:
            t8_start_notif_id = db.query(func.max(Notification.id)).scalar() or 0
            res_t8 = run_daily_markdown_job(db)  # WITHOUT now!
            print(f"      Result: {res_t8}")
            
            created_batch_ids = {
                n.batch_id for n in db.query(Notification).filter(
                    Notification.id > t8_start_notif_id,
                    Notification.alert_date == derived_date
                ).all()
            }
            
            expected_batch_ids = set()
            for s in db.query(Store).all():
                alerts = evaluate_store_spoilage_alerts(db, s.id, as_of_date=derived_date)
                for a in alerts:
                    if a.get("status") != "accepted":
                        b_id = a.get("batch_id")
                        if not b_id:
                            parts = a["id"].split("-")
                            b_id = "-".join(parts[2:]) if len(parts) >= 3 else a["id"]
                        expected_batch_ids.add(b_id)

            print(f"      Created batch_ids: {sorted(list(created_batch_ids))}")
            print(f"      Expected batch_ids: {sorted(list(expected_batch_ids))}")
            assert len(created_batch_ids) > 0, "Expected at least 1 notification created in T8"
            assert created_batch_ids == expected_batch_ids, f"Mismatch: {created_batch_ids} != {expected_batch_ids}"
            print("      [PASSED] T8: run_daily_markdown_job without now correctly uses settings.get_effective_today().")
        finally:
            settings.get_effective_today = orig_fn

    finally:
        # Mandatory cleanup: remove ONLY rows created during this test run
        print("\n[CLEANUP] Purging test-created notifications and alert actions...")
        deleted_notifs = (
            db.query(Notification)
            .filter(Notification.id > initial_notif_max_id)
            .delete(synchronize_session=False)
        )
        deleted_actions = (
            db.query(AlertAction)
            .filter(AlertAction.id > initial_action_max_id)
            .delete(synchronize_session=False)
        )
        db.commit()

        final_notif_count = db.query(Notification).count()
        final_action_count = db.query(AlertAction).count()
        assert final_notif_count == initial_notif_count, (
            f"Notification count mismatch: {final_notif_count} != {initial_notif_count}"
        )
        assert final_action_count == initial_action_count, (
            f"AlertAction count mismatch: {final_action_count} != {initial_action_count}"
        )

        db.close()
        print(f"      Cleaned up {deleted_notifs} notifications and {deleted_actions} alert actions.")
        print(f"      Surviving rows verified: {final_notif_count} notifications, {final_action_count} alert actions.")

    print("\n" + "=" * 75)
    print("ALL LEVEL 3 BACKEND TESTS PASSED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
