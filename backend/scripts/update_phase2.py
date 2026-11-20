import os
import re

backend_dir = r"F:\Development\Projects\Mobile-Apps\backend"

# 1. Update analytics.py
analytics_path = os.path.join(backend_dir, "app", "api", "v1", "endpoints", "analytics.py")
with open(analytics_path, "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace(
    "from app.core.security import get_current_user, require_roles",
    "from app.core.security import get_current_user, require_roles, verify_branch_access"
)
c = c.replace(
    'current_user: dict = Depends(require_roles("storeManager", "systemAdmin"))',
    'current_user: dict = Depends(require_roles("manager", "admin"))'
)
c = c.replace(
    "store = db.query(Store).filter(Store.id == store_id).first()",
    "target_store_id = verify_branch_access(current_user, store_id)\n    store = db.query(Store).filter(Store.id == target_store_id).first()"
)
c = c.replace("evaluate_store_spoilage_alerts(db, store_id=store_id)", "evaluate_store_spoilage_alerts(db, store_id=target_store_id)")
c = c.replace("ReplenishmentOrder.store_id == store_id", "ReplenishmentOrder.store_id == target_store_id")
c = c.replace("generate_store_recommendations(db, store_id=store_id,", "generate_store_recommendations(db, store_id=target_store_id,")
c = c.replace("Product.store_id == store_id", "Product.store_id == target_store_id")
c = c.replace("WasteLog.store_id == store_id", "WasteLog.store_id == target_store_id")
c = c.replace('detail=f"Store with ID {store_id} not found"', 'detail=f"Store with ID {target_store_id} not found"')

with open(analytics_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(c)
print("Updated analytics.py")

# 2. Update notifications.py
notif_path = os.path.join(backend_dir, "app", "api", "v1", "endpoints", "notifications.py")
with open(notif_path, "r", encoding="utf-8") as f:
    nc = f.read()

nc = nc.replace(
    "from app.core.security import require_roles",
    "from app.core.security import require_roles, verify_branch_access"
)
nc = nc.replace(
    'current_user: dict = Depends(require_roles("storeManager"))',
    'current_user: dict = Depends(require_roles("manager", "admin"))'
)
nc = nc.replace(
    "unread_count = (",
    "target_store_id = verify_branch_access(current_user, store_id)\n    unread_count = ("
)
nc = nc.replace("Notification.store_id == store_id", "Notification.store_id == target_store_id")

with open(notif_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(nc)
print("Updated notifications.py")

# 3. Update seed_db.py with clerk, auditor, manager, admin
seed_path = os.path.join(backend_dir, "seed_db.py")
with open(seed_path, "r", encoding="utf-8") as f:
    sc = f.read()

old_users_block = '''users_data = [
            {
                "username": "manager",
                "email": "manager@zerowaste.com",
                "hashed_password": get_password_hash("password123"),
                "full_name": "Store Manager",
                "role": "storeManager",
                "store_id": 1,
            },
            {
                "username": "auditor",
                "email": "auditor@zerowaste.com",
                "hashed_password": get_password_hash("auditor123"),
                "full_name": "Inventory Auditor",
                "role": "inventoryAuditor",
                "store_id": 1,
            },
            {
                "username": "admin",
                "email": "admin@zerowaste.com",
                "hashed_password": get_password_hash("admin123"),
                "full_name": "System Admin",
                "role": "systemAdmin",
                "store_id": None,
            },
        ]'''

new_users_block = '''users_data = [
            {
                "username": "clerk",
                "email": "clerk@zerowaste.com",
                "hashed_password": get_password_hash("clerk123"),
                "full_name": "Inventory Clerk",
                "role": "clerk",
                "store_id": 1,
            },
            {
                "username": "auditor",
                "email": "auditor@zerowaste.com",
                "hashed_password": get_password_hash("auditor123"),
                "full_name": "Inventory Auditor",
                "role": "auditor",
                "store_id": 1,
            },
            {
                "username": "manager",
                "email": "manager@zerowaste.com",
                "hashed_password": get_password_hash("password123"),
                "full_name": "Store Manager",
                "role": "manager",
                "store_id": 1,
            },
            {
                "username": "admin",
                "email": "admin@zerowaste.com",
                "hashed_password": get_password_hash("admin123"),
                "full_name": "Enterprise Admin",
                "role": "admin",
                "store_id": None,
            },
        ]'''

if old_users_block in sc:
    sc = sc.replace(old_users_block, new_users_block)
    with open(seed_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(sc)
    print("Updated seed_db.py")
else:
    print("Warning: old_users_block not found in seed_db.py (may already be updated or whitespace mismatch)")

# 4. Update import_dataset.py with clerk, auditor, manager, admin
import_path = os.path.join(backend_dir, "import_dataset.py")
with open(import_path, "r", encoding="utf-8") as f:
    ic = f.read()

old_ic_block = '''users_data = [
            {"username": "manager", "email": "manager@zerowaste.com", "hashed_password": get_password_hash("password123"), "full_name": "Store Manager", "role": "storeManager", "store_id": 1},
            {"username": "auditor", "email": "auditor@zerowaste.com", "hashed_password": get_password_hash("auditor123"), "full_name": "Inventory Auditor", "role": "inventoryAuditor", "store_id": 1},
            {"username": "admin", "email": "admin@zerowaste.com", "hashed_password": get_password_hash("admin123"), "full_name": "System Admin", "role": "systemAdmin", "store_id": None},
        ]'''

new_ic_block = '''users_data = [
            {"username": "clerk", "email": "clerk@zerowaste.com", "hashed_password": get_password_hash("clerk123"), "full_name": "Inventory Clerk", "role": "clerk", "store_id": 1},
            {"username": "auditor", "email": "auditor@zerowaste.com", "hashed_password": get_password_hash("auditor123"), "full_name": "Inventory Auditor", "role": "auditor", "store_id": 1},
            {"username": "manager", "email": "manager@zerowaste.com", "hashed_password": get_password_hash("password123"), "full_name": "Store Manager", "role": "manager", "store_id": 1},
            {"username": "admin", "email": "admin@zerowaste.com", "hashed_password": get_password_hash("admin123"), "full_name": "Enterprise Admin", "role": "admin", "store_id": None},
        ]'''

if old_ic_block in ic:
    ic = ic.replace(old_ic_block, new_ic_block)
    with open(import_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(ic)
    print("Updated import_dataset.py")

print("All updates prepared!")
