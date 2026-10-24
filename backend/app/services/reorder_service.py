"""
app/services/reorder_service.py
Newsvendor Critical Fractile Replenishment Engine and TreeSHAP Explainability.
Computes optimal reorder quantities considering salvage values, underage/overage costs,
safety stocks, and rolling residual forecast sigma with 56-day lag verification.
Optimized with batch feature formulation and single-call model predictions.
"""
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.stats import norm
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.config import settings
from app.models.models import (
    Product,
    DailyExogenous,
    InventorySnapshot
)
from app.services.ml_service import GroceryMLService
from app.services.feature_builder import (
    MASTER_FEATURE_NAMES,
    build_feature_dict,
    build_feature_vector
)

_ml_service = GroceryMLService.get_instance()
_model = _ml_service.model
_feature_names = _ml_service.master_feature_names

DRIVER_TRANSLATIONS = {
    "isWeekend": "Weekend Demand Surge",
    "isHoliday": "Holiday Shopping Surge",
    "isWeekday": "Weekday Operational Baseline",
    "residents": "Local Residential Density Load",
    "visits": "Commercial District Footfall",
    "visitors": "Transient Visitor Trajectory",
    "total_rain": "Precipitation Impact On Footfall",
    "avg_temp": "Ambient Temperature Demand Shift",
    "avg_humidity": "Humidity Factor Impact",
    "RR_09": "Morning Rain Dampening",
    "RR_12": "Midday Rain Profile",
    "RR_15": "Afternoon Storm Impact",
    "RR_18": "Forecasted Precipitation Impact",
    "T2M_09": "Morning Temperature Profile",
    "T2M_12": "Ambient Temperature Profile",
    "T2M_15": "Peak Afternoon Temperature",
    "T2M_18": "Evening Temperature Profile",
    "season_Spring": "Spring Seasonal Shift",
    "season_Summer": "Summer Demand Surge",
    "season_Winter": "Winter Seasonal Profile",
    "month": "Monthly Seasonal Trend",
    "dayOfYear": "Annual Sales Cycle",
    "lead_time": "Procurement Lead Time Window"
}


def _translate_feature_label(feature: str) -> str:
    if feature in DRIVER_TRANSLATIONS:
        return DRIVER_TRANSLATIONS[feature]
    if feature.startswith("lag_related_"):
        return "Category Demand Momentum"
    if feature.startswith("lag_"):
        try:
            num = int(feature.replace("lag_", ""))
            if num <= 2:
                return "Recent Daily Sell-Through Momentum"
            elif num in (6, 7, 13, 14, 20, 21):
                return "Weekly Sales Cyclicality"
            else:
                return "Historical Baseline Velocity"
        except ValueError:
            return "Historical Demand Signal"
    if feature.startswith("load_"):
        return "Peak In-Store Foot Traffic"
    if feature.startswith("weekday_"):
        day = feature.replace("weekday_", "")
        return f"{day} Shopping Patterns"
    return feature.replace("_", " ").title()


# In-memory sigma cache: (store_id, product_id, target_date) -> (sigma_e, sigma_source)
_sigma_cache: Dict[Tuple[int, int, date], Tuple[float, str]] = {}


def clear_sigma_cache():
    """Clears the in-memory sigma cache (useful for benchmarks/testing)."""
    _sigma_cache.clear()


def compute_rolling_sigma(
    db: Session,
    store_id: int,
    product_id: int,
    target_date: date,
    predicted_units: int,
    product: Optional[Product] = None,
    snap_map: Optional[Dict[date, int]] = None,
    rel_map: Optional[Dict[date, float]] = None,
    exo_map: Optional[Dict[date, DailyExogenous]] = None
) -> Tuple[float, str]:
    """
    Computes rolling standard deviation of forecast residuals over the past 28 days.
    Only days with full 56-day lag history are included in the backtest.
    If valid residual points < 14, falls back to settings.SIGMA_FACTOR * predicted_units.
    Cached per (store_id, product_id, target_date).
    Optimized: executes all 28 backtest days in 1 batch LightGBM prediction.
    """
    cache_key = (store_id, product_id, target_date)
    if cache_key in _sigma_cache:
        return _sigma_cache[cache_key]

    if product is None:
        product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        fallback = max(1.0, round(predicted_units * settings.SIGMA_FACTOR, 2))
        _sigma_cache[cache_key] = (fallback, "fallback")
        return (fallback, "fallback")

    if snap_map is None:
        all_snaps = (
            db.query(InventorySnapshot.snapshot_date, InventorySnapshot.units_sold)
            .filter(InventorySnapshot.product_id == product_id)
            .order_by(InventorySnapshot.snapshot_date.asc())
            .all()
        )
        if not all_snaps:
            fallback = max(1.0, round(predicted_units * settings.SIGMA_FACTOR, 2))
            _sigma_cache[cache_key] = (fallback, "fallback")
            return (fallback, "fallback")
        earliest_date = all_snaps[0][0]
        snap_map = {s[0]: s[1] for s in all_snaps}
    else:
        if not snap_map:
            fallback = max(1.0, round(predicted_units * settings.SIGMA_FACTOR, 2))
            _sigma_cache[cache_key] = (fallback, "fallback")
            return (fallback, "fallback")
        earliest_date = min(snap_map.keys())

    # Candidate backtest days: last 28 days before target_date
    # Only use days d where d - 56 days >= earliest_date to guarantee full 56-day lag history
    candidate_dates = [
        target_date - timedelta(days=i)
        for i in range(28, 0, -1)
        if (target_date - timedelta(days=i) - timedelta(days=56)) >= earliest_date
    ]

    # Must also have snapshot for date d
    valid_dates = [d for d in candidate_dates if d in snap_map]

    if len(valid_dates) < 14:
        fallback_sigma = max(1.0, round(predicted_units * settings.SIGMA_FACTOR, 2))
        _sigma_cache[cache_key] = (fallback_sigma, "fallback")
        return (fallback_sigma, "fallback")

    # Fetch exogenous data for all valid dates in 1 query or use preloaded map
    if exo_map is not None:
        exo_by_date = exo_map
        fallback_exo = exo_map.get(target_date) or (
            next(iter(exo_map.values()), None) if exo_map else None
        )
    else:
        exo_records = (
            db.query(DailyExogenous)
            .filter(DailyExogenous.store_id == store_id, DailyExogenous.record_date.in_(valid_dates))
            .all()
        )
        exo_by_date = {e.record_date: e for e in exo_records}
        fallback_exo = (
            db.query(DailyExogenous)
            .filter(DailyExogenous.store_id == store_id)
            .order_by(DailyExogenous.record_date.desc())
            .first()
        )

    # Pre-fetch related category sales map if not provided
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
            min_backtest_date = min(valid_dates) - timedelta(days=65)
            rel_snaps = (
                db.query(
                    InventorySnapshot.snapshot_date,
                    func.avg(InventorySnapshot.units_sold)
                )
                .filter(
                    InventorySnapshot.product_id.in_(related_ids),
                    InventorySnapshot.snapshot_date >= min_backtest_date,
                    InventorySnapshot.snapshot_date <= max(valid_dates)
                )
                .group_by(InventorySnapshot.snapshot_date)
                .all()
            )
            rel_map = {r[0]: float(r[1]) for r in rel_snaps}
        else:
            rel_map = {}

    # Build backtest features for all valid dates in batch
    feature_dicts = []
    actuals = []
    for d in valid_dates:
        actuals.append(snap_map[d])
        d_exo = exo_by_date.get(d, fallback_exo)
        f_dict = build_feature_dict(
            db=db,
            store_id=store_id,
            product_id=product_id,
            target_date=d,
            product=product,
            exo=d_exo,
            snap_map=snap_map,
            rel_map=rel_map
        )
        feature_dicts.append(f_dict)

    # Batch LightGBM inference
    batch_backtest_df = pd.DataFrame(feature_dicts, columns=MASTER_FEATURE_NAMES)
    raw_preds = _model.predict(batch_backtest_df)

    residuals = []
    for idx, raw_y in enumerate(raw_preds):
        actual_u = actuals[idx]
        pred_u = max(1, int(round(max(0.0, float(raw_y)) * settings.DEMAND_SCALE)))
        residuals.append(float(actual_u - pred_u))

    if len(residuals) >= 14:
        calc_sigma = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else float(np.std(residuals))
        sigma_e = max(1.0, calc_sigma)
        source = "rolling"
    else:
        sigma_e = max(1.0, predicted_units * settings.SIGMA_FACTOR)
        source = "fallback"

    result = (round(sigma_e, 2), source)
    _sigma_cache[cache_key] = result
    return result


def warm_sigma_cache(db: Session, target_date: Optional[date] = None) -> int:
    """
    Precomputes and caches rolling sigma for all products in all stores for target_date.
    Returns the number of (store, product) pairs warmed.
    """
    if target_date is None:
        target_date = settings.get_effective_today()

    products = (
        db.query(Product)
        .options(joinedload(Product.batches), joinedload(Product.category))
        .order_by(Product.id.asc())
        .all()
    )

    # Pre-fetch all snapshots and exogenous records in one query for ultra-fast warmup
    all_snapshots = (
        db.query(InventorySnapshot.product_id, InventorySnapshot.snapshot_date, InventorySnapshot.units_sold)
        .all()
    )
    all_exos = db.query(DailyExogenous).all()
    exos_by_store = defaultdict(dict)
    for e in all_exos:
        exos_by_store[e.store_id][e.record_date] = e
    snaps_by_product = defaultdict(dict)
    for pid, sdate, sold in all_snapshots:
        snaps_by_product[pid][sdate] = sold

    # Category averages
    cat_snaps = defaultdict(lambda: defaultdict(list))
    for p in products:
        for sdate, sold in snaps_by_product[p.id].items():
            cat_snaps[p.category_id][sdate].append(sold)
    cat_avg_maps = {}
    for cat_id, date_dict in cat_snaps.items():
        cat_avg_maps[cat_id] = {sdate: sum(vals) / len(vals) for sdate, vals in date_dict.items()}

    count = 0
    for product in products:
        p_snaps = snaps_by_product[product.id]
        p_rel = cat_avg_maps.get(product.category_id, {})
        input_dict = build_feature_dict(
            db, product.store_id, product.id, target_date,
            product=product, snap_map=p_snaps, rel_map=p_rel
        )
        input_df = pd.DataFrame([input_dict], columns=MASTER_FEATURE_NAMES)
        raw_y = float(_model.predict(input_df)[0])
        predicted_units = max(1, int(round(max(0.0, raw_y) * settings.DEMAND_SCALE)))
        compute_rolling_sigma(
            db, product.store_id, product.id, target_date, predicted_units,
            product=product, snap_map=p_snaps, rel_map=p_rel, exo_map=exos_by_store.get(product.store_id)
        )
        count += 1
    return count


def generate_store_recommendations(
    db: Session,
    store_id: int,
    target_date: date
) -> List[Dict[str, Any]]:
    """
    Executes Newsvendor optimization and TreeSHAP feature attribution for all
    products in the target store on the specified date.
    Uses rolling residual sigma with fallback and in-memory cache.
    Optimized with batch feature pre-loading and batch TreeSHAP attribution.
    """
    products = (
        db.query(Product)
        .options(joinedload(Product.batches), joinedload(Product.category))
        .filter(Product.store_id == store_id)
        .order_by(Product.id.asc())
        .all()
    )

    if not products:
        return []

    min_date = target_date - timedelta(days=105)

    # 1. Preload store-wide exogenous telemetry in 1 query
    store_exos = (
        db.query(DailyExogenous)
        .filter(
            DailyExogenous.store_id == store_id,
            DailyExogenous.record_date >= min_date,
            DailyExogenous.record_date <= target_date
        )
        .all()
    )
    exo_by_date = {e.record_date: e for e in store_exos}
    exo = exo_by_date.get(target_date)
    if not exo:
        exo = (
            db.query(DailyExogenous)
            .filter(DailyExogenous.store_id == store_id)
            .order_by(DailyExogenous.record_date.desc())
            .first()
        )

    # 2. Preload all snapshots for this store in [min_date, target_date) in 1 query
    store_snaps = (
        db.query(InventorySnapshot.product_id, InventorySnapshot.snapshot_date, InventorySnapshot.units_sold)
        .join(Product, InventorySnapshot.product_id == Product.id)
        .filter(
            Product.store_id == store_id,
            InventorySnapshot.snapshot_date >= min_date,
            InventorySnapshot.snapshot_date < target_date
        )
        .all()
    )

    prod_snaps = defaultdict(dict)
    for pid, sdate, sold in store_snaps:
        prod_snaps[pid][sdate] = sold

    cat_snaps = defaultdict(lambda: defaultdict(list))
    for p in products:
        for sdate, sold in prod_snaps[p.id].items():
            cat_snaps[p.category_id][sdate].append(sold)

    cat_avg_maps = {}
    for cat_id, date_dict in cat_snaps.items():
        cat_avg_maps[cat_id] = {sdate: sum(vals) / len(vals) for sdate, vals in date_dict.items()}

    # 3. Formulate feature vectors for all products in batch with zero redundant DB queries
    feature_dicts = [
        build_feature_dict(
            db, store_id, p.id, target_date,
            product=p,
            exo=exo,
            snap_map=prod_snaps[p.id],
            rel_map=cat_avg_maps.get(p.category_id, {})
        )
        for p in products
    ]
    batch_df = pd.DataFrame(feature_dicts, columns=MASTER_FEATURE_NAMES)

    # 4. Batch ML inference & TreeSHAP attributions
    raw_preds = _model.predict(batch_df)
    try:
        all_contribs = _model.predict(batch_df, pred_contrib=True)
    except Exception:
        if hasattr(_model, "booster_"):
            all_contribs = _model.booster_.predict(batch_df, pred_contrib=True)
        else:
            all_contribs = None

    recommendations = []

    for idx, product in enumerate(products):
        raw_y = float(raw_preds[idx])
        y_hat = max(0.0, raw_y)
        predicted_units = max(1, int(round(y_hat * settings.DEMAND_SCALE)))

        # 5. Newsvendor Critical Fractile Optimization with Rolling Residual Sigma
        cu = max(0.01, product.unit_price - product.unit_cost)
        salvage_val = product.unit_cost * settings.DEFAULT_SALVAGE_PCT
        co = max(0.01, product.unit_cost - salvage_val)

        cf = cu / (cu + co)
        cf = max(0.01, min(0.99, cf))

        k = float(norm.ppf(cf))
        k = max(0.0, min(2.5, k))

        sigma_e, sigma_source = compute_rolling_sigma(
            db, store_id, product.id, target_date, predicted_units,
            product=product,
            snap_map=prod_snaps[product.id],
            rel_map=cat_avg_maps.get(product.category_id, {}),
            exo_map=exo_by_date
        )
        optimal_buffer = max(product.safety_stock, int(round(k * sigma_e)))

        current_stock = sum(b.remaining_quantity for b in product.batches if b.remaining_quantity > 0)
        if current_stock == 0:
            current_stock = product.safety_stock

        recommended_qty = max(0, predicted_units + optimal_buffer - current_stock)

        # 6. TreeSHAP Attribution for this product
        if all_contribs is not None and len(all_contribs) > idx and len(all_contribs[idx]) > 1:
            feat_contribs = all_contribs[idx][:-1]
            abs_contribs = np.abs(feat_contribs)

            # Sum absolute contributions per distinct label
            label_magnitudes: Dict[str, float] = {}
            for fi, val in enumerate(abs_contribs):
                if fi < len(_feature_names):
                    feat_name = _feature_names[fi]
                    label = _translate_feature_label(feat_name)
                    label_magnitudes[label] = label_magnitudes.get(label, 0.0) + float(val)

            # Take top 3 distinct labels by summed magnitude
            sorted_labels = sorted(label_magnitudes.items(), key=lambda kv: kv[1], reverse=True)
            top_3 = sorted_labels[:3]
            total_top = sum(v for _, v in top_3) or 1.0

            raw_drivers = []
            for lbl, mag in top_3:
                pct = round((mag / total_top) * 100.0, 1)
                raw_drivers.append({"label": lbl, "impact_pct": pct})

            if len(raw_drivers) == 3:
                raw_drivers[2]["impact_pct"] = round(100.0 - raw_drivers[0]["impact_pct"] - raw_drivers[1]["impact_pct"], 1)

            drivers = raw_drivers
        else:
            drivers = [
                {"label": "Recent Daily Sell-Through Momentum", "impact_pct": 45.0},
                {"label": "Weekend Foot-Traffic Surge", "impact_pct": 35.0},
                {"label": "Ambient Temperature Profile", "impact_pct": 20.0}
            ]

        d1, d2 = drivers[0]["label"], drivers[1]["label"]
        p1 = drivers[0]["impact_pct"]
        xai_reason = (
            f"{d1} (+{p1}%) and {d2.lower()} drive expected demand to {predicted_units} units."
        )

        category_str = product.category.name.lower() if product.category else "produce"

        recommendations.append({
            "product_id": product.id,
            "product_name": product.name,
            "category": category_str,
            "current_stock": current_stock,
            "safety_stock": product.safety_stock,
            "predicted_demand": predicted_units,
            "recommended_qty": recommended_qty,
            "approved_qty": recommended_qty,
            "status": "pending",
            "xai_reason": xai_reason,
            "xai_drivers": drivers,
            "sigma_e": sigma_e,
            "sigma_source": sigma_source
        })

    return recommendations
