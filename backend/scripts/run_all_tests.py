import os
import sys
import subprocess

backend_dir = r"F:\Development\Projects\Mobile-Apps\backend"
python_exe = os.path.join(backend_dir, ".venv", "Scripts", "python.exe")

tests = [
    "test_ml.py",
    "test_ml_v2.py",
    "test_config_scale.py",
    "test_b3.py",
    "test_real_data.py",
    "test_sigma.py",
    "test_notifications.py",
    "test_api.py"
]

all_passed = True
print("=" * 70)
print("RUNNING ALL BACKEND TEST SUITES")
print("=" * 70)

for t in tests:
    env = os.environ.copy()
    if t in ["test_real_data.py"]:
        env["DB_NAME"] = "zerowaste_real.db"
    else:
        env["DB_NAME"] = "zerowaste.db"
    
    res = subprocess.run([python_exe, t], cwd=backend_dir, env=env, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[PASS] {t:<25}")
    else:
        print(f"[FAIL] {t:<25} (exit code {res.returncode})")
        print("--- STDOUT ---")
        print(res.stdout[-600:])
        print("--- STDERR ---")
        print(res.stderr[-600:])
        all_passed = False

print("=" * 70)
if all_passed:
    print("ALL 8 BACKEND TEST SUITES PASSED 100%!")
else:
    print("SOME TESTS FAILED.")
print("=" * 70)

sys.exit(0 if all_passed else 1)
