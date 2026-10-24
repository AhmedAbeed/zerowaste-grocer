"""
test_sigma.py
Verification suite for Rolling Residual Sigma (Level 1).
Tests:
1. Rolling sigma computation with full historical data -> sigma_source == "rolling" and sigma_e >= 1.0.
2. Fallback behavior when history is artificially limited (< 14 days) -> sigma_source == "fallback".
3. Latency comparison: Cold-start calculation time vs. Cached retrieval time (< 150 ms per item, < 300 ms for store).
"""
import time
from datetime import date, timedelta
from app.db.session import SessionLocal
from app.models.models import Store, Product, InventorySnapshot
from app.services.reorder_service import (
    compute_rolling_sigma,
    clear_sigma_cache,
    warm_sigma_cache,
    generate_store_recommendations,
    _sigma_cache
)

def test_rolling_sigma():
    print("=" * 70)
    print("ZeroWaste Grocer - Level 1: Rolling Residual Sigma Test Suite")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Clear cache first for deterministic testing
        clear_sigma_cache()

        today = date.today()

        # -------------------------------------------------------------
        # Test 1: Rolling Sigma with Full 100-Day History
        # -------------------------------------------------------------
        print("\n[Test 1/3] Verifying Rolling Sigma with Full 100-Day History...")
        sigma_val, source = compute_rolling_sigma(db, store_id=1, product_id=1, target_date=today, predicted_units=24)
        print(f"      Store 1, Product 1 -> sigma_e: {sigma_val}, source: '{source}'")
        assert source == "rolling", f"Expected 'rolling' source, got '{source}'"
        assert sigma_val >= 1.0, f"Expected sigma_e >= 1.0, got {sigma_val}"
        print("      [PASSED] Rolling sigma computed successfully from historical residuals.")

        # -------------------------------------------------------------
        # Test 2: Fallback when Historical Residuals < 14 Days
        # -------------------------------------------------------------
        print("\n[Test 2/3] Verifying Fallback Behavior when History < 14 Days...")
        past_target = today - timedelta(days=70)
        clear_sigma_cache()
        fallback_val, fallback_src = compute_rolling_sigma(db, store_id=1, product_id=1, target_date=past_target, predicted_units=20)
        print(f"      Store 1, Product 1 (Target: {past_target}) -> sigma_e: {fallback_val}, source: '{fallback_src}'")
        assert fallback_src == "fallback", f"Expected 'fallback' source, got '{fallback_src}'"
        assert fallback_val >= 1.0, f"Expected sigma_e >= 1.0, got {fallback_val}"
        print("      [PASSED] Fallback mechanism triggered correctly when data < 14 days.")

        # -------------------------------------------------------------
        # Test 3: Latency Comparison (Cold-Start vs. Cached Retrieval)
        # -------------------------------------------------------------
        print("\n[Test 3/3] Benchmarking Cold-Start vs. Cached Latency...")
        clear_sigma_cache()

        # 3a. Cold-start calculation for today (15 products in Store 1)
        t0 = time.perf_counter()
        recs_cold = generate_store_recommendations(db, store_id=1, target_date=today)
        cold_time_ms = (time.perf_counter() - t0) * 1000.0
        print(f"      Today Cold-start latency (15 products, 28-day backtest): {cold_time_ms:.2f} ms")

        # 3b. Cached retrieval for today (15 products in Store 1)
        t1 = time.perf_counter()
        recs_cached = generate_store_recommendations(db, store_id=1, target_date=today)
        cached_time_ms = (time.perf_counter() - t1) * 1000.0
        print(f"      Today Cached recommendation latency (15 products): {cached_time_ms:.2f} ms")

        # 3c. Cold-start and cached calculation for tomorrow (today + 1)
        tomorrow = today + timedelta(days=1)
        t_tom_cold = time.perf_counter()
        recs_tom_cold = generate_store_recommendations(db, store_id=1, target_date=tomorrow)
        tom_cold_ms = (time.perf_counter() - t_tom_cold) * 1000.0
        print(f"      Tomorrow Cold-start latency (15 products, 28-day backtest): {tom_cold_ms:.2f} ms")

        t_tom_cached = time.perf_counter()
        recs_tom_cached = generate_store_recommendations(db, store_id=1, target_date=tomorrow)
        tom_cached_ms = (time.perf_counter() - t_tom_cached) * 1000.0
        print(f"      Tomorrow Cached recommendation latency (15 products): {tom_cached_ms:.2f} ms")

        # 3d. Single product cached inference latency
        t2 = time.perf_counter()
        sigma_single, _ = compute_rolling_sigma(db, store_id=1, product_id=1, target_date=today, predicted_units=24)
        single_cached_ms = (time.perf_counter() - t2) * 1000.0
        print(f"      Single product cached sigma lookup latency: {single_cached_ms:.4f} ms")

        # Assertions
        assert cold_time_ms < 300.0, f"Today cold recommendations took {cold_time_ms:.2f} ms (expected < 300 ms)"
        assert cached_time_ms < 300.0, f"Today cached recommendations took {cached_time_ms:.2f} ms (expected < 300 ms)"
        assert tom_cold_ms < 300.0, f"Tomorrow cold recommendations took {tom_cold_ms:.2f} ms (expected < 300 ms)"
        assert tom_cached_ms < 300.0, f"Tomorrow cached recommendations took {tom_cached_ms:.2f} ms (expected < 300 ms)"
        assert single_cached_ms < 150.0, f"Single cached lookup took {single_cached_ms:.2f} ms (expected < 150 ms)"

        # Check that returned recommendations contain the new fields
        for r in recs_cached:
            assert "sigma_e" in r, "Missing 'sigma_e' in recommendation"
            assert "sigma_source" in r, "Missing 'sigma_source' in recommendation"
            assert r["sigma_source"] in ("rolling", "fallback"), f"Invalid source: {r['sigma_source']}"

        sample = recs_cached[0]
        print(f"      Sample Output: {sample['product_name']} | Pred: {sample['predicted_demand']} | sigma_e: {sample['sigma_e']} ({sample['sigma_source']}) | Reorder: {sample['recommended_qty']}")
        print(f"      [PASSED] Latency check: Cold = {cold_time_ms:.2f} ms (Tom Cold: {tom_cold_ms:.2f} ms) | Cached = {cached_time_ms:.2f} ms (Tom Cached: {tom_cached_ms:.2f} ms).")

        # -------------------------------------------------------------
        # Test 4: Pre-warming Cache Functionality (Today + Tomorrow)
        # -------------------------------------------------------------
        clear_sigma_cache()
        t_warm_start = time.perf_counter()
        w1 = warm_sigma_cache(db, today)
        w2 = warm_sigma_cache(db, tomorrow)
        warm_duration_ms = (time.perf_counter() - t_warm_start) * 1000.0
        print(f"\n[Cache Pre-Warm] Pre-warmed {w1 + w2} items (today + tomorrow) across all stores in {warm_duration_ms:.2f} ms")
        assert w1 == 45, f"Expected 45 products warmed for today, got {w1}"
        assert w2 == 45, f"Expected 45 products warmed for tomorrow, got {w2}"

        # Post-warming latency should immediately be fast for tomorrow
        t3 = time.perf_counter()
        recs_post_warm = generate_store_recommendations(db, store_id=2, target_date=tomorrow)
        post_warm_ms = (time.perf_counter() - t3) * 1000.0
        print(f"      Store 2 tomorrow latency post-warm: {post_warm_ms:.2f} ms (Expected < 300 ms)")
        assert post_warm_ms < 300.0, f"Store 2 tomorrow took {post_warm_ms:.2f} ms"

        print("\n" + "=" * 70)
        print("ALL LEVEL 1 SIGMA TESTS AND BENCHMARKS PASSED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    test_rolling_sigma()
