import os, sys, shutil, hashlib, urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
GOLDEN = BASE / "db_golden"
SUMS = GOLDEN / "SHA256SUMS.txt"

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1) as resp:
        if resp.status == 200:
            print("ERROR: Backend is running on port 8000. Stop it before resetting.")
            sys.exit(1)
except Exception:
    pass

expected = dict(line.strip().split()[::-1] for line in open(SUMS) if line.strip())

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while c := f.read(65536): h.update(c)
    return h.hexdigest().lower()

for g_name, t_name in [("zerowaste_real.golden.db", "zerowaste_real.db"), ("zerowaste.golden.db", "zerowaste.db")]:
    dst = BASE / t_name
    shutil.copy2(GOLDEN / g_name, dst)
    h = sha256(dst)
    exp = expected.get(t_name, "").lower()
    print(f"Reset {t_name} -> SHA-256: {h} (Matches golden: {h == exp})")
    if h != exp:
        sys.exit(f"Hash mismatch on {t_name}")

print("Databases successfully reset to golden state.")
