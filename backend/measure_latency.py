"""
measure_latency.py
Automated Latency Measurement & Performance Profiler for ZeroWaste Grocer.
Measures cold-start vs cached recommendation response times, cache pre-warming duration,
and per-item sigma lookup speeds against target SLOs (< 300 ms for store, < 150 ms for item).
"""
import time
from datetime import date
from app.db.session import SessionLocal
from app.services.reorder_service import (
    generate_store_recommendations,
    warm_sigma_cache,
    clear_sigma_cache,
    compute_rolling_sigma
)

def run_latency_benchmark():
    print("=" * 70)
    print("ZeroWaste Grocer - Latency & Performance Benchmark Profiler")
    print("=" * 70)

    db = SessionLocal()
    try:
        from datetime import timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # 1. Cold-start benchmark for today and tomorrow (empty sigma cache)
        clear_sigma_cache()
        t0 = time.perf_counter()
        recs_cold_today = generate_store_recommendations(db, store_id=1, target_date=today)
        cold_today_ms = (time.perf_counter() - t0) * 1000.0

        t0_tom = time.perf_counter()
        recs_cold_tom = generate_store_recommendations(db, store_id=1, target_date=tomorrow)
        cold_tom_ms = (time.perf_counter() - t0_tom) * 1000.0

        print(f"\n[1] Cold-Start Recommendations (Store 1, 15 items):")
        print(f"    Today Latency:    {cold_today_ms:.2f} ms ({'PASS < 300 ms' if cold_today_ms < 300.0 else 'WARN > 300 ms'})")
        print(f"    Tomorrow Latency: {cold_tom_ms:.2f} ms ({'PASS < 300 ms' if cold_tom_ms < 300.0 else 'WARN > 300 ms'})")

        # 2. Sigma Cache Pre-Warming benchmark (today + tomorrow)
        clear_sigma_cache()
        t_warm_start = time.perf_counter()
        w1 = warm_sigma_cache(db, today)
        w2 = warm_sigma_cache(db, tomorrow)
        warm_time_ms = (time.perf_counter() - t_warm_start) * 1000.0
        warmed_count = w1 + w2
        print(f"\n[2] Sigma Cache Pre-Warming (Startup Lifespan - Today + Tomorrow):")
        print(f"    Pairs warmed: {warmed_count} ({w1} today + {w2} tomorrow)")
        print(f"    Warmup duration: {warm_time_ms:.2f} ms (avg {warm_time_ms / max(1, warmed_count):.2f} ms/item)")

        # 3. Cached Recommendations benchmark for today and tomorrow
        t1 = time.perf_counter()
        recs_cached_today = generate_store_recommendations(db, store_id=1, target_date=today)
        cached_today_ms = (time.perf_counter() - t1) * 1000.0

        t1_tom = time.perf_counter()
        recs_cached_tom = generate_store_recommendations(db, store_id=1, target_date=tomorrow)
        cached_tom_ms = (time.perf_counter() - t1_tom) * 1000.0

        print(f"\n[3] Cached Recommendations (Store 1, 15 items):")
        print(f"    Today Latency:    {cached_today_ms:.2f} ms ({'PASS < 300 ms SLO' if cached_today_ms < 300.0 else 'FAIL > 300 ms'})")
        print(f"    Tomorrow Latency: {cached_tom_ms:.2f} ms ({'PASS < 300 ms SLO' if cached_tom_ms < 300.0 else 'FAIL > 300 ms'})")

        # 4. Single-Item Cached Sigma Lookup benchmark
        t2 = time.perf_counter()
        sigma_val, source = compute_rolling_sigma(db, store_id=1, product_id=1, target_date=tomorrow, predicted_units=24)
        single_item_ms = (time.perf_counter() - t2) * 1000.0
        print(f"\n[4] Single-Item Cached Sigma Lookup (Tomorrow):")
        print(f"    Latency: {single_item_ms:.4f} ms (value: {sigma_val}, source: {source})")
        print(f"    Status: {'PASS (< 150 ms SLO)' if single_item_ms < 150.0 else 'FAIL (> 150 ms)'}")

        print("\n" + "=" * 70)
        print("LATENCY SUMMARY REPORT:")
        print(f"  - Cold-Start Time (Today):      {cold_today_ms:7.2f} ms (< 300 ms SLO)")
        print(f"  - Cold-Start Time (Tomorrow):   {cold_tom_ms:7.2f} ms (< 300 ms SLO)")
        print(f"  - Cache Warmup Time (90 SKUs):  {warm_time_ms:7.2f} ms")
        print(f"  - Cached Time (Today):          {cached_today_ms:7.2f} ms (< 300 ms SLO)")
        print(f"  - Cached Time (Tomorrow):       {cached_tom_ms:7.2f} ms (< 300 ms SLO)")
        print(f"  - Single Item Lookup:           {single_item_ms:7.4f} ms (< 150 ms SLO)")
        print("=" * 70)

        assert cold_today_ms < 300.0, f"Cold today {cold_today_ms:.2f} ms exceeded 300 ms threshold!"
        assert cold_tom_ms < 300.0, f"Cold tomorrow {cold_tom_ms:.2f} ms exceeded 300 ms threshold!"
        assert cached_today_ms < 300.0, f"Cached today {cached_today_ms:.2f} ms exceeded 300 ms threshold!"
        assert cached_tom_ms < 300.0, f"Cached tomorrow {cached_tom_ms:.2f} ms exceeded 300 ms threshold!"
        assert single_item_ms < 150.0, f"Single item time {single_item_ms:.4f} ms exceeded 150 ms threshold!"

    finally:
        db.close()

if __name__ == "__main__":
    run_latency_benchmark()
