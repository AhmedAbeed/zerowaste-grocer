import sys, os
backend_dir = r"F:\Development\Projects\Mobile-Apps\backend"
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import User
from app.core.security import get_password_hash

real_db_path = os.path.join(backend_dir, "zerowaste_real.db")
if os.path.exists(real_db_path):
    eng = create_engine(f"sqlite:///{real_db_path}", connect_args={"check_same_thread": False})
    SLocal = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    db = SLocal()
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
    else:
        clerk.role = "clerk"
    db.commit()
    print("zerowaste_real.db updated successfully:")
    for u in db.query(User).all():
        print(f"ID={u.id}, User={u.username}, Role={u.role}, StoreID={u.store_id}")
    db.close()
