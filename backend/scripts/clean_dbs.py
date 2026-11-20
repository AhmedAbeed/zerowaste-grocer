import sqlite3
import os

backend_dir = r"F:\Development\Projects\Mobile-Apps\backend"
real_db = os.path.join(backend_dir, "zerowaste_real.db")

if os.path.exists(real_db):
    conn = sqlite3.connect(real_db)
    c = conn.cursor()
    c.execute("DELETE FROM product_batches WHERE id LIKE 'BATCH-TEST-%'")
    c.execute("DELETE FROM broadcasts")
    c.execute("DELETE FROM model_feedback")
    c.execute("DELETE FROM stores WHERE id > 3")
    conn.commit()
    print("Cleaned test data from zerowaste_real.db")
    conn.close()
