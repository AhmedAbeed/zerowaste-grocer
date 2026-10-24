"""
app/services/feature_builder.py
Strict 192-Feature Engineering Pipeline for ZeroWaste Grocer demand forecasting.
Constructs multi-modal feature vectors from calendar signals, ERA5 weather telemetry,
pedestrian mobility loads, and 56-day target and related sales lags.
Supports optional pre-loaded entities for ultra-fast batch recommendation formulations.
"""
from datetime import date, timedelta
import math
from typing import List, Optional, Dict
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.config import settings
from app.models.models import (
    Product,
    DailyExogenous,
    InventorySnapshot
)
from app.services.ml_service import GroceryMLService

# Retrieve ordered list of 192 feature names
_ml_service = GroceryMLService.get_instance()
MASTER_FEATURE_NAMES: List[str] = _ml_service.master_feature_names


def build_feature_dict(
    db: Session,
    store_id: int,
    product_id: int,
    target_date: date,
    product: Optional[Product] = None,
    exo: Optional[DailyExogenous] = None,
    snap_map: Optional[Dict[date, int]] = None,
    rel_map: Optional[Dict[date, float]] = None
) -> Dict[str, float]:
    """
    Constructs a dictionary mapping all 192 feature names to float values.
    Populates all 8 feature categories with zero unnecessary overhead.
    """
    feats: Dict[str, float] = {col: 0.0 for col in MASTER_FEATURE_NAMES}

    if product is None:
        product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product with ID {product_id} not found in database.")

    # --------------------------------------------------------------------------
    # 2a. Calendar Indicators [0-8]
    # --------------------------------------------------------------------------
    is_weekend = target_date.weekday() in (5, 6)
    is_weekday = target_date.weekday() < 5
    day_of_year = float(target_date.timetuple().tm_yday)
    month = float(target_date.month)

    if exo is None:
        exo = (
            db.query(DailyExogenous)
            .filter(
                DailyExogenous.store_id == store_id,
                DailyExogenous.record_date == target_date
            )
            .first()
        )
        if not exo:
            exo = (
                db.query(DailyExogenous)
                .filter(DailyExogenous.store_id == store_id)
                .order_by(DailyExogenous.record_date.desc())
                .first()
            )

    has_detailed_exo = False
    if exo is not None:
        if hasattr(exo, '__dict__') and 't2m_09' in exo.__dict__ and exo.__dict__['t2m_09'] is not None:
            has_detailed_exo = True
        elif db is not None:
            try:
                bind = db.get_bind()
                if not hasattr(bind, '_has_detailed_exo_checked'):
                    with bind.connect() as con:
                        res = con.execute(text("PRAGMA table_info(daily_exogenous)")).fetchall()
                        col_names = {r[1] for r in res}
                        bind._has_detailed_exo = "t2m_09" in col_names
                        bind._has_detailed_exo_checked = True
                if getattr(bind, '_has_detailed_exo', False):
                    has_detailed_exo = (getattr(exo, 't2m_09', None) is not None)
            except Exception:
                has_detailed_exo = False

    if has_detailed_exo:
        feats["isHoliday"] = 1.0 if (exo and exo.is_holiday) else 0.0
        feats["isBeforeHoliday"] = float(exo.is_before_holiday) if getattr(exo, 'is_before_holiday', None) is not None else 0.0
        feats["isAfterHoliday"] = float(exo.is_after_holiday) if getattr(exo, 'is_after_holiday', None) is not None else 0.0
        feats["isSchoolHoliday"] = float(exo.is_school_holiday) if getattr(exo, 'is_school_holiday', None) is not None else 0.0
        feats["isWeekend"] = float(exo.is_weekend) if getattr(exo, 'is_weekend', None) is not None else (1.0 if is_weekend else 0.0)
        feats["isWeekday"] = float(exo.is_weekday) if getattr(exo, 'is_weekday', None) is not None else (1.0 if is_weekday else 0.0)
        feats["dayOfYear"] = float(exo.day_of_year) if getattr(exo, 'day_of_year', None) is not None else day_of_year
        feats["month"] = float(exo.month_val) if getattr(exo, 'month_val', None) is not None else month
        feats["isLockdown"] = float(exo.is_lockdown) if getattr(exo, 'is_lockdown', None) is not None else 0.0

        for col_prefix in ["T2M", "TD2M", "RH2M", "P0", "GL", "UU", "VV", "RR"]:
            for hour_str in ["09", "12", "15", "18"]:
                attr_name = f"{col_prefix.lower()}_{hour_str}"
                val = getattr(exo, attr_name, None)
                feats[f"{col_prefix}_{hour_str}"] = float(val) if val is not None else 0.0

        feats["residents"] = float(exo.residents) if getattr(exo, 'residents', None) is not None else 0.0
        feats["visits"] = float(exo.visits) if getattr(exo, 'visits', None) is not None else 0.0
        feats["visitors"] = float(exo.visitors) if getattr(exo, 'visitors', None) is not None else 0.0

        for h in range(24):
            attr_name = f"load_{h:02d}"
            val = getattr(exo, attr_name, None)
            feats[attr_name] = float(val) if val is not None else 0.0
    else:
        is_holiday = 1.0 if (exo and exo.is_holiday) else 0.0

        feats["isHoliday"] = is_holiday
        feats["isBeforeHoliday"] = 0.0
        feats["isAfterHoliday"] = 0.0
        feats["isSchoolHoliday"] = 0.0
        feats["isWeekend"] = 1.0 if is_weekend else 0.0
        feats["isWeekday"] = 1.0 if is_weekday else 0.0
        feats["dayOfYear"] = day_of_year
        feats["month"] = month
        feats["isLockdown"] = 0.0

        # --------------------------------------------------------------------------
        # 2b. ERA5 Atmospheric Telemetry [9-40]
        # --------------------------------------------------------------------------
        avg_temp = float(exo.avg_temp) if exo and exo.avg_temp is not None else 21.0
        avg_humidity = float(exo.avg_humidity) if exo and exo.avg_humidity is not None else 60.0
        total_rain = float(exo.total_rain) if exo and exo.total_rain is not None else 0.0
        foot_traffic_load = float(exo.foot_traffic_load) if exo and exo.foot_traffic_load is not None else 1.0

        feats["T2M_09"] = avg_temp - 2.0
        feats["T2M_12"] = avg_temp + 2.0
        feats["T2M_15"] = avg_temp + 3.0
        feats["T2M_18"] = avg_temp

        for hour_str in ["09", "12", "15", "18"]:
            feats[f"TD2M_{hour_str}"] = avg_temp - 4.0
            feats[f"RH2M_{hour_str}"] = avg_humidity
            feats[f"P0_{hour_str}"] = 1013.25
            feats[f"GL_{hour_str}"] = 450.0
            feats[f"UU_{hour_str}"] = 1.5
            feats[f"VV_{hour_str}"] = 1.5
            feats[f"RR_{hour_str}"] = total_rain / 4.0

        # --------------------------------------------------------------------------
        # 2c. Foot Traffic & Mobility [41-43]
        # --------------------------------------------------------------------------
        feats["residents"] = 12000.0 * foot_traffic_load
        feats["visits"] = 4500.0 * foot_traffic_load
        feats["visitors"] = 2800.0 * foot_traffic_load

        # --------------------------------------------------------------------------
        # 2d. Hourly Activity Distribution [44-67]
        # --------------------------------------------------------------------------
        for h in range(24):
            bell_curve = math.exp(-((h - 14.5) ** 2) / (2.0 * (4.0 ** 2)))
            feats[f"load_{h:02d}"] = float(bell_curve * foot_traffic_load)

    # --------------------------------------------------------------------------
    # 2e. Target SKU Sales Lags [68-123] (lag_1 to lag_56)
    # --------------------------------------------------------------------------
    min_date = target_date - timedelta(days=65)

    if snap_map is None:
        target_snapshots = (
            db.query(InventorySnapshot)
            .filter(
                InventorySnapshot.product_id == product_id,
                InventorySnapshot.snapshot_date < target_date,
                InventorySnapshot.snapshot_date >= min_date
            )
            .order_by(InventorySnapshot.snapshot_date.desc())
            .all()
        )
        snap_map = {s.snapshot_date: s.units_sold for s in target_snapshots}

    if snap_map:
        avg_units = sum(snap_map.values()) / len(snap_map)
        default_lag = float(avg_units) / settings.DEMAND_SCALE
    else:
        default_lag = 0.08

    for i in range(1, 57):
        date_i = target_date - timedelta(days=i)
        if date_i in snap_map:
            feats[f"lag_{i}"] = float(snap_map[date_i]) / settings.DEMAND_SCALE
        else:
            feats[f"lag_{i}"] = default_lag

    # --------------------------------------------------------------------------
    # 2f. Related Category Sales Lags [124-179] (lag_related_1 to lag_related_56)
    # --------------------------------------------------------------------------
    if rel_map is None:
        related_prods = (
            db.query(Product.id)
            .filter(
                Product.store_id == store_id,
                Product.category_id == product.category_id,
                Product.id != product_id
            )
            .all()
        )
        related_ids = [r[0] for r in related_prods]

        if related_ids:
            rel_snaps = (
                db.query(
                    InventorySnapshot.snapshot_date,
                    func.avg(InventorySnapshot.units_sold)
                )
                .filter(
                    InventorySnapshot.product_id.in_(related_ids),
                    InventorySnapshot.snapshot_date < target_date,
                    InventorySnapshot.snapshot_date >= min_date
                )
                .group_by(InventorySnapshot.snapshot_date)
                .all()
            )
            rel_map = {r[0]: float(r[1]) for r in rel_snaps}

    if rel_map:
        for i in range(1, 57):
            date_i = target_date - timedelta(days=i)
            if date_i in rel_map:
                feats[f"lag_related_{i}"] = float(rel_map[date_i]) / settings.DEMAND_SCALE
            else:
                feats[f"lag_related_{i}"] = feats[f"lag_{i}"]
    else:
        for i in range(1, 57):
            feats[f"lag_related_{i}"] = feats[f"lag_{i}"]

    # --------------------------------------------------------------------------
    # 2g. Primary Entities [180-182]
    # --------------------------------------------------------------------------
    ml_product_id = float(((product.id - 1) % 15) + 1)
    feats["store_id"] = float(store_id)
    feats["product_id"] = ml_product_id
    feats["lead_time"] = 0.0

    # --------------------------------------------------------------------------
    # 2h. One-Hot Categoricals [183-191]
    # --------------------------------------------------------------------------
    m = target_date.month
    feats["season_Spring"] = 1.0 if m in (3, 4, 5) else 0.0
    feats["season_Summer"] = 1.0 if m in (6, 7, 8) else 0.0
    feats["season_Winter"] = 1.0 if m in (12, 1, 2) else 0.0

    w = target_date.weekday()
    feats["weekday_Monday"] = 1.0 if w == 0 else 0.0
    feats["weekday_Tuesday"] = 1.0 if w == 1 else 0.0
    feats["weekday_Wednesday"] = 1.0 if w == 2 else 0.0
    feats["weekday_Thursday"] = 1.0 if w == 3 else 0.0
    feats["weekday_Saturday"] = 1.0 if w == 5 else 0.0
    feats["weekday_Sunday"] = 1.0 if w == 6 else 0.0

    return feats


def build_feature_vector(
    db: Session,
    store_id: int,
    product_id: int,
    target_date: date,
    product: Optional[Product] = None,
    exo: Optional[DailyExogenous] = None,
    snap_map: Optional[Dict[date, int]] = None,
    rel_map: Optional[Dict[date, float]] = None
) -> pd.DataFrame:
    """
    Constructs a 1-row pandas DataFrame with 0.0 for all 192 columns in the exact
    order of master_feature_names.joblib and populates all 8 feature categories.
    Accepts optional preloaded product, exo, snap_map, and rel_map for high performance.
    """
    feats = build_feature_dict(
        db=db,
        store_id=store_id,
        product_id=product_id,
        target_date=target_date,
        product=product,
        exo=exo,
        snap_map=snap_map,
        rel_map=rel_map
    )
    return pd.DataFrame([feats], columns=MASTER_FEATURE_NAMES, dtype=float)
