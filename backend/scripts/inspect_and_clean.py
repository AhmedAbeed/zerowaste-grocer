import sqlite3
import os
from datetime import date

backend_dir = r"F:\Development\Projects\Mobile-Apps\backend"

real_db_path = os.path.join(backend_dir, "zerowaste_real.db")
if os.path.exists(real_db_path):
    conn = sqlite3.connect(real_db_path)
    c = conn.cursor()
    c.execute("DELETE FROM product_batches WHERE id LIKE 'BATCH-TEST-%'")
    c.execute("DELETE FROM broadcasts")
    c.execute("DELETE FROM model_feedback")
    c.execute("DELETE FROM stores WHERE id > 3")
    c.execute("DELETE FROM inventory_snapshots WHERE snapshot_date >= ?", (date.today().isoformat(),))
    conn.commit()
    conn.close()
    print("Cleaned zerowaste_real.db")

for db_name in ["zerowaste.db", "zerowaste_real.db"]:
    db_path = os.path.join(backend_dir, db_name)
    if not os.path.exists(db_path):
        continue
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM product_batches WHERE id LIKE 'BATCH-TEST-%'")
    b_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM broadcasts")
    bc_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM model_feedback")
    mf_cnt = c.fetchone()[0]
    c.execute("SELECT id, name FROM products WHERE id=1")
    p1 = c.fetchone()
    c.execute("SELECT SUM(remaining_quantity) FROM product_batches WHERE product_id=1")
    b_sum = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM stores")
    st_cnt = c.fetchone()[0]
    c.execute("SELECT username, role, store_id FROM users")
    users = c.fetchall()
    print(f"=== {db_name} ===")
    print(f"  test_batches: {b_cnt}")
    print(f"  broadcasts:   {bc_cnt}")
    print(f"  feedback:     {mf_cnt}")
    print(f"  product 1:    {p1} (batches total: {b_sum})")
    print(f"  stores count: {st_cnt}")
    print(f"  users:        {users}")
    conn.close()
