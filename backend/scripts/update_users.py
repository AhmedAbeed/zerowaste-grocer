import os
import sys

sys.path.insert(0, r"F:\Development\Projects\Mobile-Apps\backend")
from app.db.session import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

# Update default db (configured in settings)
db = SessionLocal()
try:
    for u in db.query(User).all():
        if u.role == "storeManager":
            u.role = "manager"
        elif u.role == "inventoryAuditor":
            u.role = "auditor"
        elif u.role == "systemAdmin":
            u.role = "admin"
    
    clerk = db.query(User).filter(User.username == "clerk").first()
    if not clerk:
        clerk = User(
            username="clerk",
            email="clerk@zerowaste.com",
            hashed_password=get_password_hash("clerk123"),
            full_name="Inventory Clerk",
            role="clerk",
            store_id=1,
            is_active=True
        )
        db.add(clerk)
        print("Added clerk user via SQLAlchemy")
    else:
        clerk.role = "clerk"
        print("Updated clerk user via SQLAlchemy")
    
    db.commit()
    print("Users in current DB:")
    for u in db.query(User).all():
        print(f"ID={u.id}, User={u.username}, Role={u.role}, StoreID={u.store_id}")
finally:
    db.close()
