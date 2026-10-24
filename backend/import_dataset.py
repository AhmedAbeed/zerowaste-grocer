"""
import_dataset.py
Imports Zenodo grocery dataset (sales_grocer{g}_{p}_0.csv) into a production-like
SQLite database (zerowaste_real.db) with 100% strict schema parity.
"""
import os
import sys
import argparse
import random
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base
from app.models.models import (
    Store,
    Category,
    Product,
    ProductBatch,
    DailyExogenous,
    InventorySnapshot,
    ReplenishmentOrder,
    OrderItem,
    WasteLog,
    User
)
from app.core.security import get_password_hash

# Ensure deterministic generation for simulated fields
random.seed(42)

def to_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    s = str(val).strip().upper()
    return s in ("TRUE", "1", "T", "YES")

def to_float(val, default: float = 0.0) -> float:
    try:
        if pd.isna(val):
            return default
        return float(val)
    except Exception:
        return default

def import_dataset(
    db_path: str = "zerowaste_real.db",
    dataset_dir: str = "data set/dataset",
    demand_scale: float = 250.0,
    as_of_date_str: str = "2023-06-30"
):
    print("=" * 70)
    print("ZeroWaste Grocer - Dataset Importer (Level 8)")
    print(f"Target DB:      {db_path}")
    print(f"Dataset Dir:    {dataset_dir}")
    print(f"Demand Scale:   {demand_scale}")
    print(f"As-of Date:     {as_of_date_str}")
    print("=" * 70)

    as_of_date = datetime.strptime(as_of_date_str, "%Y-%m-%d").date()
    db_full_path = Path(db_path)
    if not db_full_path.is_absolute():
        db_full_path = BACKEND_ROOT / db_path

    dataset_full_dir = Path(dataset_dir)
    if not dataset_full_dir.is_absolute():
        dataset_full_dir = BACKEND_ROOT / dataset_dir

    if not dataset_full_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_full_dir}")

    # Remove existing database file if present
    if db_full_path.exists():
        print(f"Removing existing database file: {db_full_path}")
        os.remove(db_full_path)

    engine = create_engine(f"sqlite:///{db_full_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. Seed Stores
        print("\n[1/6] Seeding 3 Stores...")
        stores_data = [
            {"id": 1, "name": "Metro Downtown Branch", "location": "101 Grand Ave, Central Metro", "lat": 37.7749, "lon": -122.4194},
            {"id": 2, "name": "Suburban Supercenter", "location": "450 Valley Blvd, Westside Suburbs", "lat": 37.7833, "lon": -122.4167},
            {"id": 3, "name": "Harbor Organic Market", "location": "72 Ocean View Dr, Marina Bay", "lat": 37.8080, "lon": -122.4177},
        ]
        stores = []
        for s in stores_data:
            st = Store(**s)
            db.add(st)
            stores.append(st)
        db.commit()
        print(f"      Seeded {len(stores)} stores.")

        # 2. Seed Categories
        print("[2/6] Seeding 4 Categories...")
        categories_data = [
            {"id": 1, "name": "Produce", "shelf_life_days": 7},
            {"id": 2, "name": "Dairy", "shelf_life_days": 20},
            {"id": 3, "name": "Bakery", "shelf_life_days": 4},
            {"id": 4, "name": "Butchery", "shelf_life_days": 4},
        ]
        categories = []
        for c in categories_data:
            cat = Category(**c)
            db.add(cat)
            categories.append(cat)
        db.commit()
        print(f"      Seeded {len(categories)} categories.")

        # 3. Seed Products (15 master catalog items replicated for 3 stores = 45 products)
        print("[3/6] Seeding 45 Products...")
        master_catalog = [
            {"base_id": 1, "sku": "PRD-AVO-01", "name": "Organic Hass Avocados", "cat_id": 1, "cost": 1.20, "price": 2.49, "shelf_life": 5, "safety": 15},
            {"base_id": 2, "sku": "PRD-SPN-02", "name": "Baby Spinach 200g", "cat_id": 1, "cost": 1.10, "price": 2.99, "shelf_life": 6, "safety": 12},
            {"base_id": 3, "sku": "PRD-APL-03", "name": "Honeycrisp Apples 1kg", "cat_id": 1, "cost": 1.50, "price": 3.49, "shelf_life": 14, "safety": 20},
            {"base_id": 4, "sku": "PRD-TOM-04", "name": "Roma Tomatoes 500g", "cat_id": 1, "cost": 0.90, "price": 1.99, "shelf_life": 7, "safety": 14},
            {"base_id": 5, "sku": "DAY-MLK-05", "name": "Whole Milk 1 Gallon", "cat_id": 2, "cost": 2.10, "price": 3.89, "shelf_life": 10, "safety": 15},
            {"base_id": 6, "sku": "DAY-YOG-06", "name": "Greek Yogurt Plain 500g", "cat_id": 2, "cost": 1.80, "price": 3.49, "shelf_life": 12, "safety": 12},
            {"base_id": 7, "sku": "DAY-BUT-07", "name": "Organic Salted Butter 250g", "cat_id": 2, "cost": 2.50, "price": 4.99, "shelf_life": 30, "safety": 10},
            {"base_id": 8, "sku": "DAY-CHD-08", "name": "Sharp Cheddar Block 200g", "cat_id": 2, "cost": 3.20, "price": 5.99, "shelf_life": 45, "safety": 8},
            {"base_id": 9, "sku": "BAK-SRD-09", "name": "Artisanal Sourdough Loaf", "cat_id": 3, "cost": 1.50, "price": 4.49, "shelf_life": 3, "safety": 8},
            {"base_id": 10, "sku": "BAK-CRS-10", "name": "Butter Croissants 4-Pack", "cat_id": 3, "cost": 2.20, "price": 4.99, "shelf_life": 2, "safety": 6},
            {"base_id": 11, "sku": "BAK-WGB-11", "name": "Whole Grain Sandwich Bread", "cat_id": 3, "cost": 1.40, "price": 3.79, "shelf_life": 5, "safety": 10},
            {"base_id": 12, "sku": "BAK-BRC-12", "name": "Cinnamon Brioche Buns", "cat_id": 3, "cost": 1.80, "price": 4.29, "shelf_life": 3, "safety": 6},
            {"base_id": 13, "sku": "BTC-RBX-13", "name": "Grass-fed Ribeye Steak 350g", "cat_id": 4, "cost": 8.50, "price": 16.99, "shelf_life": 4, "safety": 6},
            {"base_id": 14, "sku": "BTC-CHK-14", "name": "Organic Chicken Breast 500g", "cat_id": 4, "cost": 4.20, "price": 8.99, "shelf_life": 4, "safety": 10},
            {"base_id": 15, "sku": "BTC-GBF-15", "name": "Lean Ground Beef 90/10 500g", "cat_id": 4, "cost": 5.00, "price": 9.49, "shelf_life": 3, "safety": 8},
        ]
        products = []
        product_id_counter = 1
        for st in stores:
            for item in master_catalog:
                sku = item["sku"] if st.id == 1 else f"{item['sku']}-S{st.id}"
                p = Product(
                    id=product_id_counter,
                    store_id=st.id,
                    category_id=item["cat_id"],
                    sku=sku,
                    name=item["name"],
                    unit_cost=item["cost"],
                    unit_price=item["price"],
                    shelf_life_days=item["shelf_life"],
                    safety_stock=item["safety"],
                    is_perishable=True
                )
                db.add(p)
                products.append(p)
                product_id_counter += 1
        db.commit()
        print(f"      Seeded {len(products)} products across 3 stores.")

        # 4. Seed Staff Users for Authentication
        print("[4/6] Seeding default staff users...")
        users_data = [
            {"username": "manager", "email": "manager@zerowaste.com", "hashed_password": get_password_hash("password123"), "full_name": "Store Manager", "role": "storeManager", "store_id": 1},
            {"username": "auditor", "email": "auditor@zerowaste.com", "hashed_password": get_password_hash("auditor123"), "full_name": "Inventory Auditor", "role": "inventoryAuditor", "store_id": 1},
            {"username": "admin", "email": "admin@zerowaste.com", "hashed_password": get_password_hash("admin123"), "full_name": "System Admin", "role": "systemAdmin", "store_id": None},
        ]
        for ud in users_data:
            db.add(User(**ud))
        db.commit()
        print(f"      Seeded {len(users_data)} users.")

        # 5. Import Daily Exogenous Telemetry (1 file per grocer: sales_grocer{g}_1_0.csv)
        print("\n[5/6] Importing Daily Exogenous Telemetry (per store)...")
        total_exo = 0
        for g in [1, 2, 3]:
            exo_path = dataset_full_dir / f"sales_grocer{g}_1_0.csv"
            df_exo = pd.read_csv(exo_path)
            exo_records = []
            for _, row in df_exo.iterrows():
                rec_date = datetime.strptime(str(row["sales_date"]), "%Y-%m-%d").date()

                # Calculate legacy aggregated telemetry
                t_vals = [to_float(row.get(f"T2M_{h:02d}")) for h in [9, 12, 15, 18]]
                avg_temp = sum(t_vals) / len(t_vals)

                rh_vals = [to_float(row.get(f"RH2M_{h:02d}")) for h in [9, 12, 15, 18]]
                avg_humidity = sum(rh_vals) / len(rh_vals)

                rr_vals = [to_float(row.get(f"RR_{h:02d}")) for h in [9, 12, 15, 18]]
                total_rain = sum(rr_vals)

                load_vals = [to_float(row.get(f"load_{h:02d}")) for h in range(24)]
                foot_traffic_load = sum(load_vals) / len(load_vals) if load_vals else 1.0

                is_hol = to_bool(row.get("isHoliday", False))

                record = DailyExogenous(
                    store_id=g,
                    record_date=rec_date,
                    avg_temp=round(avg_temp, 2),
                    avg_humidity=round(avg_humidity, 2),
                    total_rain=round(total_rain, 2),
                    foot_traffic_load=round(foot_traffic_load, 4),
                    is_holiday=is_hol,
                    # Detailed calendar features
                    is_before_holiday=to_float(row.get("isBeforeHoliday")),
                    is_after_holiday=to_float(row.get("isAfterHoliday")),
                    is_school_holiday=to_float(row.get("isSchoolHoliday")),
                    is_weekend=to_float(row.get("isWeekend")),
                    is_weekday=to_float(row.get("isWeekday")),
                    day_of_year=to_float(row.get("dayOfYear")),
                    month_val=to_float(row.get("month")),
                    is_lockdown=to_float(row.get("isLockdown")),
                    # ERA5 weather features
                    t2m_09=to_float(row.get("T2M_09")), t2m_12=to_float(row.get("T2M_12")), t2m_15=to_float(row.get("T2M_15")), t2m_18=to_float(row.get("T2M_18")),
                    td2m_09=to_float(row.get("TD2M_09")), td2m_12=to_float(row.get("TD2M_12")), td2m_15=to_float(row.get("TD2M_15")), td2m_18=to_float(row.get("TD2M_18")),
                    rh2m_09=to_float(row.get("RH2M_09")), rh2m_12=to_float(row.get("RH2M_12")), rh2m_15=to_float(row.get("RH2M_15")), rh2m_18=to_float(row.get("RH2M_18")),
                    p0_09=to_float(row.get("P0_09")), p0_12=to_float(row.get("P0_12")), p0_15=to_float(row.get("P0_15")), p0_18=to_float(row.get("P0_18")),
                    gl_09=to_float(row.get("GL_09")), gl_12=to_float(row.get("GL_12")), gl_15=to_float(row.get("GL_15")), gl_18=to_float(row.get("GL_18")),
                    uu_09=to_float(row.get("UU_09")), uu_12=to_float(row.get("UU_12")), uu_15=to_float(row.get("UU_15")), uu_18=to_float(row.get("UU_18")),
                    vv_09=to_float(row.get("VV_09")), vv_12=to_float(row.get("VV_12")), vv_15=to_float(row.get("VV_15")), vv_18=to_float(row.get("VV_18")),
                    rr_09=to_float(row.get("RR_09")), rr_12=to_float(row.get("RR_12")), rr_15=to_float(row.get("RR_15")), rr_18=to_float(row.get("RR_18")),
                    # Foot traffic mobility features
                    residents=to_float(row.get("residents")),
                    visits=to_float(row.get("visits")),
                    visitors=to_float(row.get("visitors")),
                    # Diurnal pedestrian profile
                    load_00=to_float(row.get("load_00")), load_01=to_float(row.get("load_01")), load_02=to_float(row.get("load_02")), load_03=to_float(row.get("load_03")),
                    load_04=to_float(row.get("load_04")), load_05=to_float(row.get("load_05")), load_06=to_float(row.get("load_06")), load_07=to_float(row.get("load_07")),
                    load_08=to_float(row.get("load_08")), load_09=to_float(row.get("load_09")), load_10=to_float(row.get("load_10")), load_11=to_float(row.get("load_11")),
                    load_12=to_float(row.get("load_12")), load_13=to_float(row.get("load_13")), load_14=to_float(row.get("load_14")), load_15=to_float(row.get("load_15")),
                    load_16=to_float(row.get("load_16")), load_17=to_float(row.get("load_17")), load_18=to_float(row.get("load_18")), load_19=to_float(row.get("load_19")),
                    load_20=to_float(row.get("load_20")), load_21=to_float(row.get("load_21")), load_22=to_float(row.get("load_22")), load_23=to_float(row.get("load_23")),
                )
                exo_records.append(record)

            db.bulk_save_objects(exo_records)
            db.commit()
            total_exo += len(exo_records)
            print(f"      Store {g}: {len(exo_records)} daily exogenous records imported.")

        # 6. Import Inventory Snapshots (45 files: 3 stores x 15 products)
        print("\n[6/6] Importing Inventory Snapshots (45 files, lead=0)...")
        total_snapshots = 0
        recent_sales_map = {}  # (product_id, date) -> units_sold for batch simulation

        for g in [1, 2, 3]:
            for p in range(1, 16):
                file_path = dataset_full_dir / f"sales_grocer{g}_{p}_0.csv"
                db_product_id = (g - 1) * 15 + p

                df_prod = pd.read_csv(file_path, usecols=["sales_date", "sum_amount"])
                snapshots = []
                for _, row in df_prod.iterrows():
                    snap_date = datetime.strptime(str(row["sales_date"]), "%Y-%m-%d").date()
                    raw_sum = to_float(row["sum_amount"])
                    units_sold = max(0, int(round(raw_sum * demand_scale)))
                    opening_stock = units_sold + random.randint(2, 8)
                    units_spoiled = 0
                    closing_stock = max(0, opening_stock - units_sold - units_spoiled)

                    snapshots.append(InventorySnapshot(
                        product_id=db_product_id,
                        snapshot_date=snap_date,
                        opening_stock=opening_stock,
                        units_sold=units_sold,
                        units_spoiled=units_spoiled,
                        closing_stock=closing_stock
                    ))

                    # Track recent sales for active batch quantities
                    if snap_date >= as_of_date - timedelta(days=10):
                        recent_sales_map[(db_product_id, snap_date)] = units_sold

                    if len(snapshots) >= 500:
                        db.bulk_save_objects(snapshots)
                        db.commit()
                        total_snapshots += len(snapshots)
                        snapshots = []

                if snapshots:
                    db.bulk_save_objects(snapshots)
                    db.commit()
                    total_snapshots += len(snapshots)

                print(f"      Store {g}, Product {p:2d}: {len(df_prod)} snapshots imported.")

        # 7. Seed Realistic Product Batches (around as-of date for live UI demonstration)
        print("\n[7/7] Seeding realistic product batches for live UI...")
        batches = []
        for prod in products:
            base_id = ((prod.id - 1) % 15) + 1
            st_id = prod.store_id
            prefix = f"S{st_id}-" if st_id > 1 else ""

            # Ensure high urgency batches for Produce/Bakery/Butchery
            if base_id in (2, 9, 10, 13, 14):
                # Urgent batch: expires in 1-2 days from as_of_date
                batches.append(ProductBatch(
                    id=f"{prefix}B-{prod.sku[:3]}-{base_id}01-REAL",
                    product_id=prod.id,
                    received_date=as_of_date - timedelta(days=2),
                    expiration_date=as_of_date + timedelta(days=1 if base_id in (2, 10) else 2),
                    initial_quantity=75,
                    remaining_quantity=60,
                    current_discount_pct=0.0
                ))
                # Standard replenishment batch
                batches.append(ProductBatch(
                    id=f"{prefix}B-{prod.sku[:3]}-{base_id}02-REAL",
                    product_id=prod.id,
                    received_date=as_of_date - timedelta(days=1),
                    expiration_date=as_of_date + timedelta(days=prod.shelf_life_days),
                    initial_quantity=20,
                    remaining_quantity=18,
                    current_discount_pct=0.0
                ))
            else:
                batches.append(ProductBatch(
                    id=f"{prefix}B-{prod.sku[:3]}-{base_id}01-REAL",
                    product_id=prod.id,
                    received_date=as_of_date - timedelta(days=random.randint(1, 3)),
                    expiration_date=as_of_date + timedelta(days=max(3, prod.shelf_life_days - 2)),
                    initial_quantity=prod.safety_stock * 2,
                    remaining_quantity=int(prod.safety_stock * 1.5),
                    current_discount_pct=0.0
                ))

        for b in batches:
            db.add(b)
        db.commit()
        print(f"      Seeded {len(batches)} active product batches.")

        # 6. Historical Waste Logs & Replenishment Orders
        print("\n[6/6] Seeding historical waste logs and replenishment orders...")
        waste_logs = []
        for store in stores:
            store_products = [p for p in products if p.store_id == store.id and p.shelf_life_days <= 6]
            for past_days in range(1, 31, 2):
                log_date = as_of_date - timedelta(days=past_days)
                chosen_prod = random.choice(store_products)
                spoiled_qty = random.randint(1, 5)
                loss = round(spoiled_qty * chosen_prod.unit_cost, 2)
                waste_logs.append(WasteLog(
                    product_id=chosen_prod.id,
                    store_id=store.id,
                    date=log_date,
                    spoiled_quantity=spoiled_qty,
                    financial_loss=loss,
                    recorded_by="Inventory Audit System"
                ))
        db.bulk_save_objects(waste_logs)
        db.commit()
        print(f"      Seeded {len(waste_logs)} waste log entries.")

        orders_data = [
            {"store_id": 1, "order_date": as_of_date - timedelta(days=3), "delivery_date": as_of_date - timedelta(days=1), "status": "COMPLETED", "total": 245.50},
            {"store_id": 1, "order_date": as_of_date - timedelta(days=1), "delivery_date": as_of_date, "status": "APPROVED", "total": 182.20},
            {"store_id": 1, "order_date": as_of_date, "delivery_date": as_of_date + timedelta(days=1), "status": "PENDING", "total": 310.80},
            {"store_id": 2, "order_date": as_of_date, "delivery_date": as_of_date + timedelta(days=1), "status": "PENDING", "total": 290.40},
            {"store_id": 3, "order_date": as_of_date, "delivery_date": as_of_date + timedelta(days=1), "status": "PENDING", "total": 195.00},
        ]
        for od in orders_data:
            order = ReplenishmentOrder(
                store_id=od["store_id"],
                order_date=od["order_date"],
                delivery_date=od["delivery_date"],
                status=od["status"],
                total_amount=od["total"]
            )
            db.add(order)
            db.flush()
            prod_sample = [p for p in products if p.store_id == od["store_id"]][:3]
            for p in prod_sample:
                db.add(OrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    predicted_demand=round(random.uniform(12.0, 28.0), 2),
                    recommended_qty=random.randint(15, 30),
                    final_approved_qty=random.randint(15, 30),
                    xai_reason="ERA5 telemetry and historical patterns dictate 1-day lead replenishment."
                ))
        db.commit()
        print(f"      Seeded {len(orders_data)} initial replenishment orders.")

        # Compute database file metrics
        db_size_bytes = db_full_path.stat().st_size
        db_size_mb = db_size_bytes / (1024 * 1024)
        with open(db_full_path, "rb") as f:
            db_sha256 = hashlib.sha256(f.read()).hexdigest()

        print("\n" + "=" * 70)
        print("DATASET IMPORT SUMMARY & INTEGRITY VERIFICATION")
        print("=" * 70)
        counts = {
            "Stores": db.query(Store).count(),
            "Categories": db.query(Category).count(),
            "Products": db.query(Product).count(),
            "Product Batches": db.query(ProductBatch).count(),
            "Daily Exogenous": db.query(DailyExogenous).count(),
            "Inventory Snapshots": db.query(InventorySnapshot).count(),
            "Waste Logs": db.query(WasteLog).count(),
            "Replenishment Orders": db.query(ReplenishmentOrder).count(),
            "Users": db.query(User).count(),
        }
        for entity, cnt in counts.items():
            print(f"  {entity:<22} : {cnt:>8,d}")
        print("-" * 70)
        print(f"  Database Path          : {db_full_path}")
        print(f"  Database Size          : {db_size_mb:.2f} MB ({db_size_bytes:,d} bytes)")
        print(f"  Database SHA-256       : {db_sha256}")
        print("=" * 70)

        return db_sha256, db_size_mb

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Import failed: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="ZeroWaste Grocer - Dataset Importer (Level 8)")
    parser.add_argument("--db-path", type=str, default="zerowaste_real.db", help="Path to SQLite target database")
    parser.add_argument("--dataset-dir", type=str, default="data set/dataset", help="Path to raw dataset folder")
    parser.add_argument("--demand-scale", type=float, default=250.0, help="Continuous target to retail unit scaling constant")
    parser.add_argument("--as-of-date", type=str, default="2023-06-30", help="As-of historical replay date (YYYY-MM-DD)")
    args = parser.parse_args()

    import_dataset(
        db_path=args.db_path,
        dataset_dir=args.dataset_dir,
        demand_scale=args.demand_scale,
        as_of_date_str=args.as_of_date
    )

if __name__ == "__main__":
    main()
