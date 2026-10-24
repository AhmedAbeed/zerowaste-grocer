"""Deprecated wrapper for reset_db.py."""
import sys
from pathlib import Path
import subprocess

if __name__ == "__main__":
    reset_script = Path(__file__).resolve().parent / "reset_db.py"
    res = subprocess.run([sys.executable, str(reset_script)] + sys.argv[1:])
    sys.exit(res.returncode)
