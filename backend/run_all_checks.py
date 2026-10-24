import sys
import os
import time
import argparse
import subprocess
import hashlib
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import func

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal, engine
from app.models.models import Store, Notification, AlertAction

def get_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def print_failure_output(name: str, stdout: str, stderr: str):
    print(f"\n--- FAILURE in {name} ---")
    combined = (stdout or "") + ("\n" + stderr if stderr else "")
    lines = combined.strip().splitlines()
    last_lines = lines[-40:] if len(lines) > 40 else lines
    for line in last_lines:
        print(f"  {line}")
    print("-" * 50)

def main():
    os.environ["DB_NAME"] = "zerowaste.db"
    os.environ.pop("AS_OF_DATE", None)
    parser = argparse.ArgumentParser(description="Run all ZeroWaste Grocer checks")
    parser.add_argument("--flutter", action="store_true", help="Run Flutter checks (analyze, test)")
    args = parser.parse_args()

    results = []

    # Backup database before any test runs
    db_path = BACKEND_DIR / "zerowaste.db"
    temp_dir = Path(tempfile.gettempdir())
    backup_path = temp_dir / f"zerowaste_backup_{int(time.time()*1000)}.db"
    initial_sha256 = get_file_sha256(db_path)
    shutil.copy2(db_path, backup_path)

    # 1. DB Baseline capture
    db = SessionLocal()
    try:
        init_stores = db.query(Store).count()
        init_notifs = db.query(Notification).count()
        init_actions = db.query(AlertAction).count()
    finally:
        db.close()
    engine.dispose()

    restore_identical = False
    duration_restore = 0.0

    try:
        # 2. Backend test scripts
        backend_scripts = [
            "test_ml.py",
            "test_b3.py",
            "test_api.py",
            "test_sigma.py",
            "test_notifications.py",
            "measure_latency.py",
        ]

        test_env = os.environ.copy()
        test_env["DB_NAME"] = "zerowaste.db"
        test_env.pop("AS_OF_DATE", None)

        for script in backend_scripts:
            script_path = BACKEND_DIR / script
            start = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(BACKEND_DIR),
                env=test_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            duration = time.perf_counter() - start
            passed = (proc.returncode == 0)
            results.append((script, "PASS" if passed else "FAIL", f"{duration:.2f}s"))
            if not passed:
                print_failure_output(script, proc.stdout, proc.stderr)

        # 3. Flutter checks if requested
        if args.flutter:
            flutter_dir = BACKEND_DIR.parent / "app_Mena"
            flutter_checks = [
                ("flutter analyze", "flutter analyze"),
                ("flutter test", "flutter test"),
            ]
            for name, cmd in flutter_checks:
                start = time.perf_counter()
                proc = subprocess.run(
                    cmd,
                    cwd=str(flutter_dir),
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                duration = time.perf_counter() - start
                passed = (proc.returncode == 0)
                results.append((name, "PASS" if passed else "FAIL", f"{duration:.2f}s"))
                if not passed:
                    print_failure_output(name, proc.stdout, proc.stderr)

        # 4. DB verification before restore
        start_db = time.perf_counter()
        db = SessionLocal()
        try:
            final_stores = db.query(Store).count()
            final_notifs = db.query(Notification).count()
            final_actions = db.query(AlertAction).count()
        finally:
            db.close()
        engine.dispose()
        duration_db = time.perf_counter() - start_db

        store_check_pass = (final_stores == 3)
        results.append(("DB: stores == 3", "PASS" if store_check_pass else "FAIL", f"{duration_db:.2f}s"))

        notif_check_pass = (final_notifs == init_notifs and final_actions == init_actions)
        results.append(("DB: notifications/alert_actions unchanged from baseline", "PASS" if notif_check_pass else "FAIL", f"{duration_db:.2f}s"))

    finally:
        # Restore database byte-for-byte
        start_res = time.perf_counter()
        engine.dispose()
        shutil.copy2(backup_path, db_path)
        restored_sha256 = get_file_sha256(db_path)
        restore_identical = (initial_sha256 == restored_sha256)
        duration_restore = time.perf_counter() - start_res
        print(f"DB restored: sha256 identical = {restore_identical}")
        if backup_path.exists():
            try:
                backup_path.unlink()
            except Exception:
                pass

    results.append(("DB restored byte-for-byte", "PASS" if restore_identical else "FAIL", f"{duration_restore:.2f}s"))

    # 5. Print table
    col_w1 = 55
    col_w2 = 8
    col_w3 = 10
    total_w = col_w1 + col_w2 + col_w3 + 6

    print("\n" + "=" * total_w)
    hdr_check = "Check"
    hdr_result = "Result"
    hdr_sec = "Seconds"
    print(f"{hdr_check:<{col_w1}} | {hdr_result:<{col_w2}} | {hdr_sec:>{col_w3}}")
    print("-" * total_w)
    all_pass = True
    for name, res, sec in results:
        if res != "PASS":
            all_pass = False
        print(f"{name:<{col_w1}} | {res:<{col_w2}} | {sec:>{col_w3}}")
    print("=" * total_w + "\n")

    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()
