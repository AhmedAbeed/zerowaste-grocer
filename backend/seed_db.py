"""
seed_db.py
Database initialization and comprehensive mock data seeder for ZeroWaste Grocer.
Seeds 3 stores, 4 categories, 45 products, active batches, 60 days of historical
inventory snapshots & daily exogenous telemetry, waste logs, and replenishment orders.
"""
import sys
import random
import math
from datetime import date, datetime, timedelta
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.base import Base
from app.db.session import engine, SessionLocal
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

# Seed for deterministic realism
random.seed(42)

def seed():
    print("=" * 65)
    print("ZeroWaste Grocer - Database Schema Creation & Seeding")
    print("=" * 65)

    # 1. Reset database tables
    print("[1/6] Recreating database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("      All database tables created successfully.")

    db = SessionLocal()

    try:
        # 2. Seed Stores
        print("[2/6] Seeding stores...")
        stores_data = [
            {"id": 1, "name": "Metro Downtown Branch", "location": "101 Grand Ave, Central Metro", "lat": 37.7749, "lon": -122.4194},
            {"id": 2, "name": "Suburban Supercenter", "location": "450 Valley Blvd, Westside Suburbs", "lat": 37.7833, "lon": -122.4167},
            {"id": 3, "name": "Harbor Organic Market", "location": "72 Ocean View Dr, Marina Bay", "lat": 37.8080, "lon": -122.4177},
        ]
        stores = []
        for s in stores_data:
            store_obj = Store(**s)
            db.add(store_obj)
            stores.append(store_obj)
        db.commit()
        print(f"      Seeded {len(stores)} stores.")

        # 3. Seed Categories
        print("[3/6] Seeding categories...")
        categories_data = [
            {"id": 1, "name": "Produce", "shelf_life_days": 7},
            {"id": 2, "name": "Dairy", "shelf_life_days": 20},
            {"id": 3, "name": "Bakery", "shelf_life_days": 4},
            {"id": 4, "name": "Butchery", "shelf_life_days": 4},
        ]
        categories = []
        for c in categories_data:
            cat_obj = Category(**c)
            db.add(cat_obj)
            categories.append(cat_obj)
        db.commit()
        print(f"      Seeded {len(categories)} categories.")

        # 4. Seed Products (15 master catalog products duplicated for 3 stores)
        print("[4/6] Seeding products & inventory batches...")
        master_catalog = [
            # Produce (1 to 4)
            {"base_id": 1, "sku": "PRD-AVO-01", "name": "Organic Hass Avocados", "cat_id": 1, "cost": 1.20, "price": 2.49, "shelf_life": 5, "safety": 15},
            {"base_id": 2, "sku": "PRD-SPN-02", "name": "Baby Spinach 200g", "cat_id": 1, "cost": 1.10, "price": 2.99, "shelf_life": 6, "safety": 12},
            {"base_id": 3, "sku": "PRD-APL-03", "name": "Honeycrisp Apples 1kg", "cat_id": 1, "cost": 1.50, "price": 3.49, "shelf_life": 14, "safety": 20},
            {"base_id": 4, "sku": "PRD-TOM-04", "name": "Roma Tomatoes 500g", "cat_id": 1, "cost": 0.90, "price": 1.99, "shelf_life": 7, "safety": 14},

            # Dairy (5 to 8)
            {"base_id": 5, "sku": "DAY-MLK-05", "name": "Whole Milk 1 Gallon", "cat_id": 2, "cost": 2.10, "price": 3.89, "shelf_life": 10, "safety": 15},
            {"base_id": 6, "sku": "DAY-YOG-06", "name": "Greek Yogurt Plain 500g", "cat_id": 2, "cost": 1.80, "price": 3.49, "shelf_life": 12, "safety": 12},
            {"base_id": 7, "sku": "DAY-BUT-07", "name": "Organic Salted Butter 250g", "cat_id": 2, "cost": 2.50, "price": 4.99, "shelf_life": 30, "safety": 10},
            {"base_id": 8, "sku": "DAY-CHD-08", "name": "Sharp Cheddar Block 200g", "cat_id": 2, "cost": 3.20, "price": 5.99, "shelf_life": 45, "safety": 8},

            # Bakery (9 to 12)
            {"base_id": 9, "sku": "BAK-SRD-09", "name": "Artisanal Sourdough Loaf", "cat_id": 3, "cost": 1.50, "price": 4.49, "shelf_life": 3, "safety": 8},
            {"base_id": 10, "sku": "BAK-CRS-10", "name": "Butter Croissants 4-Pack", "cat_id": 3, "cost": 2.20, "price": 4.99, "shelf_life": 2, "safety": 6},
            {"base_id": 11, "sku": "BAK-WGB-11", "name": "Whole Grain Sandwich Bread", "cat_id": 3, "cost": 1.40, "price": 3.79, "shelf_life": 5, "safety": 10},
            {"base_id": 12, "sku": "BAK-BRC-12", "name": "Cinnamon Brioche Buns", "cat_id": 3, "cost": 1.80, "price": 4.29, "shelf_life": 3, "safety": 6},

            # Butchery (13 to 15)
            {"base_id": 13, "sku": "BTC-RBX-13", "name": "Grass-fed Ribeye Steak 350g", "cat_id": 4, "cost": 8.50, "price": 16.99, "shelf_life": 4, "safety": 6},
            {"base_id": 14, "sku": "BTC-CHK-14", "name": "Organic Chicken Breast 500g", "cat_id": 4, "cost": 4.20, "price": 8.99, "shelf_life": 4, "safety": 10},
            {"base_id": 15, "sku": "BTC-GBF-15", "name": "Lean Ground Beef 90/10 500g", "cat_id": 4, "cost": 5.00, "price": 9.49, "shelf_life": 3, "safety": 8},
        ]

        today = date.today()
        products = []
        batches = []

        product_id_counter = 1

        for store in stores:
            for item in master_catalog:
                prod = Product(
                    id=product_id_counter,
                    store_id=store.id,
                    category_id=item["cat_id"],
                    sku=item["sku"] if store.id == 1 else f"{item['sku']}-S{store.id}",
                    name=item["name"],
                    unit_cost=item["cost"],
                    unit_price=item["price"],
                    shelf_life_days=item["shelf_life"],
                    safety_stock=item["safety"],
                    is_perishable=True
                )
                db.add(prod)
                products.append(prod)

                base_id = item["base_id"]
                prefix = f"S{store.id}-" if store.id > 1 else ""

                # Seed batches according to requirements:
                # Urgent batches for products 2, 9, 10, 14 with expiration in 1-2 days & remaining > predicted demand
                if base_id == 2:  # Baby Spinach (urgent alert)
                    batches.append(ProductBatch(
                        id=f"{prefix}B-SPN-201",
                        product_id=product_id_counter,
                        received_date=today - timedelta(days=4),
                        expiration_date=today + timedelta(days=1),
                        initial_quantity=70,  # boosted to create realistic surplus for the spoilage-alert demo
                        remaining_quantity=70,  # boosted to create realistic surplus for the spoilage-alert demo
                        current_discount_pct=0.0
                    ))
                    batches.append(ProductBatch(
                        id=f"{prefix}B-SPN-202",
                        product_id=product_id_counter,
                        received_date=today - timedelta(days=1),
                        expiration_date=today + timedelta(days=5),
                        initial_quantity=15,
                        remaining_quantity=8,
                        current_discount_pct=0.0
                    ))
                elif base_id == 9:  # Artisanal Sourdough (urgent batch - regular stock, no alert)
                    batches.append(ProductBatch(
                        id=f"{prefix}B-SRD-901",
                        product_id=product_id_counter,
                        received_date=today - timedelta(days=1),
                        expiration_date=today + timedelta(days=2),
                        initial_quantity=15,
                        remaining_quantity=6,
                        current_discount_pct=0.0
                    ))
                    batches.append(ProductBatch(
                        id=f"{prefix}B-SRD-902",
                        product_id=product_id_counter,
                        received_date=today,
                        expiration_date=today + timedelta(days=3),
                        initial_quantity=10,
                        remaining_quantity=6,
                        current_discount_pct=0.0
                    ))
                elif base_id == 10:  # Butter Croissants (urgent alert)
                    batches.append(ProductBatch(
                        id=f"{prefix}B-CRS-1001",
                        product_id=product_id_counter,
                        received_date=today - timedelta(days=1),
                        expiration_date=today + timedelta(days=1),
                        initial_quantity=70,  # boosted to create realistic surplus for the spoilage-alert demo
                        remaining_quantity=70,  # boosted to create realistic surplus for the spoilage-alert demo
                        current_discount_pct=0.0
                    ))
                    batches.append(ProductBatch(
                        id=f"{prefix}B-CRS-1002",
                        product_id=product_id_counter,
                        received_date=today,
                        expiration_date=today + timedelta(days=2),
                        initial_quantity=8,
                        remaining_quantity=3,
                        current_discount_pct=0.0
                    ))
                elif base_id == 13:  # Grass-fed Ribeye Steak (urgent alert)
                    batches.append(ProductBatch(
                        id=f"{prefix}B-BTC-1301",
                        product_id=product_id_counter,
                        received_date=today - timedelta(days=2),
                        expiration_date=today + timedelta(days=2),
                        initial_quantity=110,  # boosted to create realistic surplus for the spoilage-alert demo
                        remaining_quantity=110,  # boosted to create realistic surplus for the spoilage-alert demo
                        current_discount_pct=0.0
                    ))
                elif base_id == 14:  # Chicken Breast (urgent alert)
                    batches.append(ProductBatch(
                        id=f"{prefix}B-CHK-1401",
                        product_id=product_id_counter,
                        received_date=today - timedelta(days=2),
                        expiration_date=today + timedelta(days=2),
                        initial_quantity=110,  # boosted to create realistic surplus for the spoilage-alert demo
                        remaining_quantity=110,  # boosted to create realistic surplus for the spoilage-alert demo
                        current_discount_pct=0.0
                    ))
                    batches.append(ProductBatch(
                        id=f"{prefix}B-CHK-1402",
                        product_id=product_id_counter,
                        received_date=today,
                        expiration_date=today + timedelta(days=4),
                        initial_quantity=15,
                        remaining_quantity=10,
                        current_discount_pct=0.0
                    ))
                else:
                    # Regular active batches
                    batches.append(ProductBatch(
                        id=f"{prefix}B-{item['sku'][:3]}-{base_id}01",
                        product_id=product_id_counter,
                        received_date=today - timedelta(days=random.randint(1, 3)),
                        expiration_date=today + timedelta(days=max(3, item["shelf_life"] - 1)),
                        initial_quantity=item["safety"] * 2,
                        remaining_quantity=int(item["safety"] * 1.4),
                        current_discount_pct=0.0
                    ))

                product_id_counter += 1

        db.commit()
        for b in batches:
            db.add(b)
        db.commit()
        print(f"      Seeded {len(products)} products across 3 stores.")
        print(f"      Seeded {len(batches)} product batches (including urgent alert candidates).")

        # 5. 60 Days of Historical Snapshots & Exogenous Telemetry (CRITICAL for ML lags)
        print("[5/6] Seeding 60+ days of historical inventory snapshots & daily exogenous...")
        days_history = 100
        start_date = today - timedelta(days=days_history)

        snapshots = []
        exogenous_records = []

        # Generate daily exogenous for each store across 61 days
        for day_offset in range(days_history + 1):
            current_date = start_date + timedelta(days=day_offset)
            is_weekend = current_date.weekday() in (5, 6)

            # Seasonal/periodic variation
            t = day_offset / 30.0
            base_temp = 21.0 + 4.0 * math.sin(t)
            base_humidity = 60.0 + 12.0 * math.cos(t)

            for store in stores:
                # Slight micro-climate difference per store
                store_temp_offset = (store.id - 2) * 1.2
                temp = round(base_temp + store_temp_offset + random.uniform(-1.5, 1.5), 2)
                humidity = round(base_humidity + random.uniform(-5.0, 5.0), 2)

                # Rainfall probability (approx 20% of days)
                has_rain = (day_offset % 7 == 2) or (random.random() < 0.15)
                rain_amount = round(random.uniform(2.5, 18.0), 2) if has_rain else 0.0

                # Foot traffic load (weekend surge: 1.15 to 1.45, weekday: 0.70 to 0.95)
                if is_weekend:
                    traffic = round(random.uniform(1.15, 1.45), 4)
                else:
                    traffic = round(random.uniform(0.70, 0.95), 4)

                is_hol = is_weekend or (day_offset in [10, 35, 50])

                exogenous_records.append(DailyExogenous(
                    store_id=store.id,
                    record_date=current_date,
                    avg_temp=temp,
                    avg_humidity=humidity,
                    total_rain=rain_amount,
                    foot_traffic_load=traffic,
                    is_holiday=is_hol
                ))

        db.bulk_save_objects(exogenous_records)
        db.commit()
        print(f"      Seeded {len(exogenous_records)} daily exogenous telemetry records.")

        # Generate 60 days of inventory snapshots for each product
        # Track simulated rolling inventory per product
        current_stocks = {p.id: p.safety_stock * 2 for p in products}

        for day_offset in range(days_history + 1):
            current_date = start_date + timedelta(days=day_offset)
            is_weekend = current_date.weekday() in (5, 6)

            for p in products:
                # Target demand / units sold (between 5 and 35 per day)
                # Weekends see +40% surge, high-velocity items (milk, avocados, croissants) sell more
                base_sales = random.randint(8, 22)
                if p.category_id in [1, 2]:  # Produce & Dairy high velocity
                    base_sales += random.randint(3, 8)
                if is_weekend:
                    base_sales = int(base_sales * 1.35)

                units_sold = max(5, min(35, base_sales))

                # Occasional spoilage for highly perishable products
                units_spoiled = 0
                if p.shelf_life_days <= 4 and random.random() < 0.20:
                    units_spoiled = random.randint(1, 3)

                opening = current_stocks[p.id]

                # If stock was too low, simulate arrival of replenishment shipment
                if opening < units_sold + units_spoiled:
                    opening += p.safety_stock * 2

                closing = max(0, opening - units_sold - units_spoiled)

                # Next day opening includes replenishment when below safety stock
                next_opening = closing
                if next_opening < p.safety_stock:
                    next_opening += p.safety_stock * 2

                current_stocks[p.id] = next_opening

                snapshots.append(InventorySnapshot(
                    product_id=p.id,
                    snapshot_date=current_date,
                    opening_stock=opening,
                    units_sold=units_sold,
                    units_spoiled=units_spoiled,
                    closing_stock=closing
                ))

        db.bulk_save_objects(snapshots)
        db.commit()
        print(f"      Seeded {len(snapshots)} daily inventory snapshots.")

        # 6. Waste Logs & Replenishment Orders
        print("[6/6] Seeding waste logs & replenishment orders...")
        waste_logs = []
        for store in stores:
            # Past 30 days of waste logs for perishable SKUs
            store_products = [p for p in products if p.store_id == store.id and p.shelf_life_days <= 6]
            for past_days in range(1, 31, 2):
                log_date = today - timedelta(days=past_days)
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

        # Initial replenishment orders
        orders_data = [
            {"store_id": 1, "order_date": today - timedelta(days=3), "delivery_date": today - timedelta(days=1), "status": "COMPLETED", "total": 245.50},
            {"store_id": 1, "order_date": today - timedelta(days=1), "delivery_date": today, "status": "APPROVED", "total": 182.20},
            {"store_id": 1, "order_date": today, "delivery_date": today + timedelta(days=1), "status": "PENDING", "total": 310.80},
            {"store_id": 2, "order_date": today, "delivery_date": today + timedelta(days=1), "status": "PENDING", "total": 290.40},
            {"store_id": 3, "order_date": today, "delivery_date": today + timedelta(days=1), "status": "PENDING", "total": 215.00},
        ]

        order_objs = []
        for od in orders_data:
            ord_obj = ReplenishmentOrder(
                store_id=od["store_id"],
                order_date=od["order_date"],
                delivery_date=od["delivery_date"],
                status=od["status"],
                total_amount=od["total"]
            )
            db.add(ord_obj)
            order_objs.append(ord_obj)
        db.commit()

        # Seed items for each order
        order_items = []
        for ord_obj in order_objs:
            store_prods = [p for p in products if p.store_id == ord_obj.store_id]
            for p in store_prods[:4]:
                order_items.append(OrderItem(
                    order_id=ord_obj.id,
                    product_id=p.id,
                    predicted_demand=round(random.uniform(12.0, 28.0), 2),
                    recommended_qty=random.randint(15, 30),
                    final_approved_qty=random.randint(15, 30),
                    xai_reason="Foot-traffic load expected to surge +18% on weekend; 1-day lead time."
                ))

        for item in order_items:
            db.add(item)
        db.commit()
        print(f"      Seeded {len(order_objs)} orders with {len(order_items)} line items.")

        # 7. Seed Staff Users for RBAC
        print("[7/7] Seeding staff users with RBAC roles...")
        users_data = [
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
        ]
        for ud in users_data:
            existing_user = db.query(User).filter(User.username == ud["username"]).first()
            if not existing_user:
                db.add(User(**ud))
        db.commit()
        print(f"      Seeded {len(users_data)} staff users for RBAC.")

        # Print final verification table counts
        print("=" * 65)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 65)
        counts = {
            "stores": db.query(Store).count(),
            "categories": db.query(Category).count(),
            "products": db.query(Product).count(),
            "product_batches": db.query(ProductBatch).count(),
            "daily_exogenous": db.query(DailyExogenous).count(),
            "inventory_snapshots": db.query(InventorySnapshot).count(),
            "replenishment_orders": db.query(ReplenishmentOrder).count(),
            "order_items": db.query(OrderItem).count(),
            "waste_logs": db.query(WasteLog).count(),
            "users": db.query(User).count(),
        }

        print(f"{'Table Name':<25} | {'Record Count':<12}")
        print("-" * 40)
        for tbl, cnt in counts.items():
            print(f"{tbl:<25} | {cnt:<12}")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()

