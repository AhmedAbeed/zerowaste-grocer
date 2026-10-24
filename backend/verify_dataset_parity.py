"""
verify_dataset_parity.py
Level 6 Part 2: Comprehensive Read-Only Dataset Parity Verification.
Reads from 'backend/data set/dataset' and prints console verification tables without modifying any files.
"""
import os
import sys
import glob
from pathlib import Path
import numpy as np
import pandas as pd

# Add backend root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Step 2.0: Reuse exact model loader from ml_service
from app.services.ml_service import GroceryMLService

DATASET_DIR = BASE_DIR / "data set" / "dataset"

def run_step_2_0(service):
    print("=" * 80)
    print("STEP 2.0 - ML Model Loader & Inference Verification")
    print("=" * 80)
    print(f"Model Loader: GroceryMLService.get_instance()")
    print(f"Model Object: {type(service.model)}")
    print(f"Artifact Paths: MODEL_PATH={service.model}, FEATURE_NAMES_PATH count={len(service.master_feature_names)}")
    print(f"Input Type: pandas.DataFrame with exact column ordering matching master_feature_names (192 columns)")
    print(f"NaN Handling: Passed directly as np.nan to LightGBM model.predict() (LightGBM natively handles NaNs along default split paths)")
    print(f"Prediction Call: service.model.predict(input_df)")


def load_45_lead0_files(service):
    master = service.master_feature_names
    records = [] # (g, p, df_raw, X_192)
    
    for g in [1, 2, 3]:
        for p in range(1, 16):
            fname = f"sales_grocer{g}_{p}_0.csv"
            fpath = DATASET_DIR / fname
            if not fpath.exists():
                raise FileNotFoundError(f"Dataset file missing: {fpath}")
            
            df = pd.read_csv(fpath)
            
            # Step 2.1: Build 192 features in exact order of master_feature_names
            data_dict = {}
            for col in master:
                if col == "store_id":
                    data_dict[col] = np.full(len(df), float(g))
                elif col == "product_id":
                    data_dict[col] = np.full(len(df), float(p))
                elif col == "lead_time":
                    data_dict[col] = np.zeros(len(df), dtype=float)
                elif col.startswith("season_"):
                    s_name = col.replace("season_", "")
                    data_dict[col] = (df["season"] == s_name).astype(float).values
                elif col.startswith("weekday_"):
                    w_name = col.replace("weekday_", "")
                    data_dict[col] = (df["weekday"] == w_name).astype(float).values
                else:
                    # Shared column from CSV
                    s = df[col]
                    if s.dtype == bool:
                        data_dict[col] = s.astype(float).values
                    elif s.dtype == object:
                        if s.isin(["TRUE", "FALSE", True, False]).all():
                            data_dict[col] = s.replace({"TRUE": 1.0, "FALSE": 0.0, True: 1.0, False: 0.0}).astype(float).values
                        else:
                            data_dict[col] = pd.to_numeric(s, errors="coerce").values
                    else:
                        data_dict[col] = s.astype(float).values
            
            X_192 = pd.DataFrame(data_dict, columns=master)
            assert list(X_192.columns) == master, f"Column mismatch in {fname}"
            records.append((g, p, fname, df, X_192))
            
    return records


def run_step_2_1(records, master):
    print("\n" + "=" * 80)
    print("STEP 2.1 - Feature Alignment & Master Feature Names Parity Check")
    print("=" * 80)
    print(f"Total lead 0 files verified: {len(records)} files (grocers 1..3, products 1..15)")
    for g, p, fname, df, X in records:
        assert list(X.columns) == master, f"Column list mismatch in {fname}"
    print(f"ASSERTION PASSED: All 45 files have exactly 192 features strictly aligned with master_feature_names.")


def run_step_2_2(records, service):
    print("\n" + "=" * 80)
    print("STEP 2.2 - Prediction Metrics on Rows with lag_56 not null")
    print("=" * 80)
    
    all_y = []
    all_pred = []
    all_dates = []
    all_grocers = []
    
    for g, p, fname, df, X in records:
        mask = df["lag_56"].notna()
        y_valid = df.loc[mask, "sum_amount"].values
        X_valid = X.loc[mask]
        dates_valid = df.loc[mask, "sales_date"].values
        
        preds = service.model.predict(X_valid)
        preds = np.maximum(0.0, preds)
        
        all_y.extend(y_valid)
        all_pred.extend(preds)
        all_dates.extend(dates_valid)
        all_grocers.extend([g] * len(y_valid))
        
    all_y = np.array(all_y)
    all_pred = np.array(all_pred)
    all_dates = pd.to_datetime(all_dates)
    all_grocers = np.array(all_grocers)
    
    def calc_metrics(y, p):
        wape = np.sum(np.abs(y - p)) / np.sum(y) if np.sum(y) > 0 else 0.0
        mae = np.mean(np.abs(y - p))
        bias = np.sum(p) / np.sum(y) if np.sum(y) > 0 else 0.0
        return wape, mae, bias
    
    # (i) Overall Table
    w_ov, m_ov, b_ov = calc_metrics(all_y, all_pred)
    print("\n(i) OVERALL METRICS (lag_56 not null, 45 files):")
    print(f"{'Metric':<25} | {'Value':<15}")
    print("-" * 43)
    print(f"{'Total Evaluated Rows':<25} | {len(all_y):<15}")
    print(f"{'WAPE':<25} | {w_ov:.4f} ({w_ov*100:.2f}%)")
    print(f"{'MAE':<25} | {m_ov:.6f}")
    print(f"{'Bias Ratio (sum p/sum y)':<25} | {b_ov:.4f}")

    # (ii) Table by Period
    print("\n(ii) METRICS BY PERIOD:")
    print(f"{'Period':<15} | {'Rows':<8} | {'WAPE':<10} | {'MAE':<10} | {'Bias Ratio':<12}")
    print("-" * 63)
    periods = [
        ("2020", (all_dates.year == 2020)),
        ("2021", (all_dates.year == 2021)),
        ("2022", (all_dates.year == 2022)),
        ("2023-H1", (all_dates.year == 2023) & (all_dates.month <= 6))
    ]
    for pname, pmask in periods:
        w, m, b = calc_metrics(all_y[pmask], all_pred[pmask])
        print(f"{pname:<15} | {int(np.sum(pmask)):<8} | {w:.4f}    | {m:.6f} | {b:.4f}")

    # (iii) Table by Grocer
    print("\n(iii) METRICS BY GROCER:")
    print(f"{'Grocer':<15} | {'Rows':<8} | {'WAPE':<10} | {'MAE':<10} | {'Bias Ratio':<12}")
    print("-" * 63)
    for g in [1, 2, 3]:
        gmask = (all_grocers == g)
        w, m, b = calc_metrics(all_y[gmask], all_pred[gmask])
        print(f"Grocer {g:<8} | {int(np.sum(gmask)):<8} | {w:.4f}    | {m:.6f} | {b:.4f}")


def run_step_2_3(records, service):
    print("\n" + "=" * 80)
    print("STEP 2.3 - Mapping Check on Grocer 1 (2023-01-01 to 2023-06-30)")
    print("=" * 80)
    
    g1_records = [r for r in records if r[0] == 1]
    
    # Collect data for rows from 2023-01-01 to 2023-06-30 where lag_56 not null
    def evaluate_variant(variant_mode):
        y_list = []
        pred_list = []
        for g, p, fname, df, X in g1_records:
            mask = (df["sales_date"] >= "2023-01-01") & (df["sales_date"] <= "2023-06-30") & (df["lag_56"].notna())
            y_sub = df.loc[mask, "sum_amount"].values
            X_sub = X.loc[mask].copy()
            
            if variant_mode == "correct":
                X_sub["store_id"] = float(g)
                X_sub["product_id"] = float(p)
            elif variant_mode == "swapped_prod":
                X_sub["store_id"] = float(g)
                X_sub["product_id"] = float((p % 15) + 1)
            elif variant_mode == "swapped_store":
                X_sub["store_id"] = float((g % 3) + 1)
                X_sub["product_id"] = float(p)
                
            preds = service.model.predict(X_sub)
            preds = np.maximum(0.0, preds)
            y_list.extend(y_sub)
            pred_list.extend(preds)
            
        y_arr = np.array(y_list)
        pred_arr = np.array(pred_list)
        wape = np.sum(np.abs(y_arr - pred_arr)) / np.sum(y_arr)
        mae = np.mean(np.abs(y_arr - pred_arr))
        return wape, mae, len(y_arr)

    w_a, m_a, n = evaluate_variant("correct")
    w_b, m_b, _ = evaluate_variant("swapped_prod")
    w_c, m_c, _ = evaluate_variant("swapped_store")

    print(f"{'Variant':<45} | {'WAPE':<10} | {'MAE':<10} | {'Rows'}")
    print("-" * 75)
    print(f"(a) Correct IDs (store_id=g, product_id=p)   | {w_a:.4f}    | {m_a:.6f} | {n}")
    print(f"(b) Swapped product_id = (p % 15) + 1       | {w_b:.4f}    | {m_b:.6f} | {n}")
    print(f"(c) Swapped store_id = (g % 3) + 1          | {w_c:.4f}    | {m_c:.6f} | {n}")


def run_step_2_4(records):
    print("\n" + "=" * 80)
    print("STEP 2.4 - Target Scaling per File (45 lead-0 files)")
    print("=" * 80)
    print(f"{'File Name':<24} | {'Min':<8} | {'Max':<8} | {'Mean':<10} | {'Std':<10} | {'Zero Days %':<12}")
    print("-" * 80)
    for g, p, fname, df, X in records:
        s = df["sum_amount"]
        zero_pct = (s == 0.0).sum() / len(s) * 100.0
        print(f"{fname:<24} | {s.min():<8.4f} | {s.max():<8.4f} | {s.mean():<10.6f} | {s.std():<10.6f} | {zero_pct:<11.2f}%")


def run_step_2_5(records):
    print("\n" + "=" * 80)
    print("STEP 2.5 - Exogenous Telemetry Consistency")
    print("=" * 80)
    
    # Identify exogenous columns
    df_sample = records[0][3]
    exo_cols = []
    for c in df_sample.columns:
        if any(c.startswith(prefix) for prefix in ['T2M_', 'TD2M_', 'RH2M_', 'P0_', 'GL_', 'UU_', 'VV_', 'RR_', 'load_']):
            exo_cols.append(c)
        elif c in ['isHoliday', 'isBeforeHoliday', 'isAfterHoliday', 'isSchoolHoliday', 'isWeekend', 'isWeekday', 'isLockdown', 'dayOfYear', 'month', 'residents', 'visits', 'visitors']:
            exo_cols.append(c)
            
    print(f"Exogenous columns tracked: {len(exo_cols)}")

    # 1. Grocer 1: Product 1 vs Products 2..15
    g1_dfs = {p: df for g, p, fname, df, X in records if g == 1}
    df_p1 = g1_dfs[1]
    
    print("\n--- (1) Grocer 1: Products 2..15 compared against Product 1 on same sales_date ---")
    print(f"{'Product Comparison':<25} | {'Common Dates':<14} | {'Differing Exogenous Cols':<25}")
    print("-" * 68)
    for p in range(2, 16):
        df_other = g1_dfs[p]
        merged = pd.merge(df_p1[["sales_date"] + exo_cols], df_other[["sales_date"] + exo_cols], on="sales_date", suffixes=("_1", "_p"))
        diff_count = 0
        for col in exo_cols:
            s1 = merged[col + "_1"]
            sp = merged[col + "_p"]
            if pd.api.types.is_numeric_dtype(s1):
                if not np.allclose(s1.fillna(0), sp.fillna(0), atol=1e-5):
                    diff_count += 1
            else:
                if not (s1 == sp).all():
                    diff_count += 1
        print(f"Product {p:<2} vs Product 1    | {len(merged):<14} | {diff_count} / {len(exo_cols)}")

    # 2. Cross-Grocer comparison for Product 1
    g_p1_dfs = {g: df for g, p, fname, df, X in records if p == 1}
    print("\n--- (2) Cross-Grocer Comparison (Product 1 across stores on same sales_date) ---")
    print(f"{'Pair Comparison':<35} | {'Common Dates':<14} | {'Differing Exogenous Cols':<25}")
    print("-" * 78)
    pairs = [
        ("grocer1/product1 vs grocer2/product1", 1, 2),
        ("grocer1/product1 vs grocer3/product1", 1, 3),
        ("grocer2/product1 vs grocer3/product1", 2, 3),
    ]
    for label, ga, gb in pairs:
        df_a = g_p1_dfs[ga]
        df_b = g_p1_dfs[gb]
        merged = pd.merge(df_a[["sales_date"] + exo_cols], df_b[["sales_date"] + exo_cols], on="sales_date", suffixes=("_a", "_b"))
        diff_count = 0
        for col in exo_cols:
            sa = merged[col + "_a"]
            sb = merged[col + "_b"]
            if pd.api.types.is_numeric_dtype(sa):
                if not np.allclose(sa.fillna(0), sb.fillna(0), atol=1e-5):
                    diff_count += 1
            else:
                if not (sa == sb).all():
                    diff_count += 1
        print(f"{label:<35} | {len(merged):<14} | {diff_count} / {len(exo_cols)}")


def run_step_2_6(records):
    print("\n" + "=" * 80)
    print("STEP 2.6 - lag_related Analysis (Grocer 1, Product 1, lead 0)")
    print("=" * 80)
    
    g1_dfs = {p: df for g, p, fname, df, X in records if g == 1}
    df1 = g1_dfs[1]
    all_sales = pd.DataFrame({p: g1_dfs[p]["sum_amount"] for p in range(1, 16)})
    
    for lag_k in [1, 7]:
        col_rel = f"lag_related_{lag_k}"
        col_self = f"lag_{lag_k}"
        mask = df1[col_rel].notna()
        y_rel = df1.loc[mask, col_rel]
        
        print(f"\n--- Analysis for {col_rel} (compared against day t-{lag_k}, {int(mask.sum())} valid rows) ---")
        
        # (i) sum_amount of each other single product q in 2..15
        q_results = []
        for q in range(2, 16):
            val_q = g1_dfs[q]["sum_amount"].shift(lag_k).loc[mask]
            diff = np.abs(y_rel - val_q)
            q_results.append((q, diff.mean(), diff.max()))
        q_results.sort(key=lambda x: x[1])
        
        print(f"Hypothesis (i): Single products q in 2..15 (Top 3 closest by mean abs diff):")
        for rank, (q, mean_d, max_d) in enumerate(q_results[:3], 1):
            print(f"  Rank {rank}: Product {q:<2} -> Mean Abs Diff = {mean_d:.6f}, Max Abs Diff = {max_d:.6f}")
            
        # (ii) mean sum_amount of all 15 products
        mean_all = all_sales.mean(axis=1).shift(lag_k).loc[mask]
        d_mean_all = np.abs(y_rel - mean_all)
        print(f"Hypothesis (ii): Mean of all 15 products (day t-{lag_k}):")
        print(f"  Mean Abs Diff = {d_mean_all.mean():.6f}, Max Abs Diff = {d_mean_all.max():.6f}")

        # (iii) mean of 14 other products
        mean_14 = pd.DataFrame({q: g1_dfs[q]["sum_amount"] for q in range(2, 16)}).mean(axis=1).shift(lag_k).loc[mask]
        d_mean_14 = np.abs(y_rel - mean_14)
        print(f"Hypothesis (iii): Mean of 14 other products (day t-{lag_k}):")
        print(f"  Mean Abs Diff = {d_mean_14.mean():.6f}, Max Abs Diff = {d_mean_14.max():.6f}")

        # (iv) sum of all 15 products
        sum_all = all_sales.sum(axis=1).shift(lag_k).loc[mask]
        d_sum_all = np.abs(y_rel - sum_all)
        print(f"Hypothesis (iv): Sum of all 15 products (day t-{lag_k}):")
        print(f"  Mean Abs Diff = {d_sum_all.mean():.6f}, Max Abs Diff = {d_sum_all.max():.6f}")

        # (v) lag_k of same product
        d_self = np.abs(y_rel - df1.loc[mask, col_self])
        print(f"Hypothesis (v): Same product {col_self}:")
        print(f"  Mean Abs Diff = {d_self.mean():.6f}, Max Abs Diff = {d_self.max():.6f}")


def run_step_2_7():
    print("\n" + "=" * 80)
    print("STEP 2.7 - Verbatim feature_builder.py Architecture Analysis")
    print("=" * 80)
    fb_path = BASE_DIR / "app" / "services" / "feature_builder.py"
    with open(fb_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    def quote_range(title, start, end):
        print(f"\n--- {title} (Lines {start}-{end}) ---")
        for idx in range(start, end + 1):
            print(f"{idx:03d}: {lines[idx-1]}", end="")
            
    quote_range("Target SKU Sales Lags & Missing Lag Handling (lag_1 to lag_56)", 122, 152)
    quote_range("Related Category Sales Lags (lag_related_1 to lag_related_56)", 154, 194)
    quote_range("Primary Entities (store_id, product_id, lead_time)", 196, 202)
    quote_range("One-Hot Categoricals (season_* and weekday_*)", 204, 218)


if __name__ == "__main__":
    service = GroceryMLService.get_instance()
    run_step_2_0(service)
    records = load_45_lead0_files(service)
    run_step_2_1(records, service.master_feature_names)
    run_step_2_2(records, service)
    run_step_2_3(records, service)
    run_step_2_4(records)
    run_step_2_5(records)
    run_step_2_6(records)
    run_step_2_7()
    print("\n" + "=" * 80)
    print("DATASET PARITY VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
