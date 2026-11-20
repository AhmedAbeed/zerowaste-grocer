import sys
import os

backend_dir = r"F:\Development\Projects\Mobile-Apps\backend"
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from app.db.base import Base
import app.models  # load all models including Broadcast, ModelFeedback

for db_name in ["zerowaste.db", "zerowaste_real.db"]:
    db_path = os.path.join(backend_dir, db_name)
    if os.path.exists(db_path):
        eng = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(bind=eng)
        print(f"Created all tables in {db_name}")

print("Phase 3 tables created successfully!")
