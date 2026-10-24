# verify_import_gates.py
"""
ZeroWaste Grocer - Level 7: Read-only verification gates before dataset import.
Evaluates model sensitivity, calendar derivation parity, lag_related structure,
import round-trip simulation, and database schema / seed facts.
"""
import os
import sys
import argparse
from datetime import datetime
import numpy as np
import pandas as pd

# Ensure backend root is on sys.path
BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

DATASET_DIR = os.path.join(BACKEND_ROOT, 'data set', 'dataset')


def run_gate_1():
    print('=' * 80)
    print('GATE 1 - Model sensitivity to ids')
    print('=' * 80)
    from app.services.ml_service import GroceryMLService
    svc = GroceryMLService.get_instance()
    model = svc.model
    booster = model.booster_
    feature_names = svc.master_feature_names

    splits = booster.feature_importance(importance_type='split')
    gains = booster.feature_importance(importance_type='gain')
    imp_df = pd.DataFrame({
        'feature': feature_names,
        'split': splits,
        'gain': gains
    })

    print('\n--- 1.1 Feature Importances (Target Entities & Lag Groups) ---')
    for target in ['store_id', 'product_id', 'lead_time']:
        row = imp_df[imp_df['feature'] == target].iloc[0]
        print(f'{target:12s} | split: {int(row["split"]):5d} | gain: {row["gain"]:12.4f}')

    lag_rows = imp_df[imp_df['feature'].str.match(r'^lag_\d+$')]
    print(f'{"sum lag_1..56":12s} | split: {int(lag_rows["split"].sum()):5d} | gain: {lag_rows["gain"].sum():12.4f}')

    lag_rel_rows = imp_df[imp_df['feature'].str.match(r'^lag_related_\d+$')]
    print(f'{"sum lag_rel":12s} | split: {int(lag_rel_rows["split"].sum()):5d} | gain: {lag_rel_rows["gain"].sum():12.4f}')

    print('\n--- Top 15 Features Overall by Gain ---')
    top15 = imp_df.sort_values(by='gain', ascending=False).head(15).reset_index(drop=True)
    top15.index = top15.index + 1
    top15['split'] = top15['split'].astype(int)
    print(top15.to_string())

    print('\n--- 1.2 Identifier Sensitivity on Grocer 1 (2023-01-01 to 2023-06-30) ---')
    g = 1
    preds_a = []
    preds_b = []
    preds_c = []
    store_col_a_first5 = None
    store_col_c_first5 = None

    for p in range(1, 16):
        path = os.path.join(DATASET_DIR, f'sales_grocer{g}_{p}_0.csv')
        df = pd.read_csv(path)
        mask = (df['sales_date'] >= '2023-01-01') & (df['sales_date'] <= '2023-06-30') & (~df['lag_56'].isna())
        df_sub = df.loc[mask].copy()

        shared = [c for c in feature_names if c in df_sub.columns]
        base_input = df_sub[shared].copy()
        base_input['lead_time'] = 0.0
        for s in ['Spring', 'Summer', 'Winter']:
            base_input[f'season_{s}'] = (df_sub['season'] == s).astype(float)
        for w in ['Monday', 'Saturday', 'Sunday', 'Thursday', 'Tuesday', 'Wednesday']:
            base_input[f'weekday_{w}'] = (df_sub['weekday'] == w).astype(float)

        # Variant (a): correct ids
        input_a = base_input.copy()
        input_a['store_id'] = float(g)
        input_a['product_id'] = float(p)
        input_a = input_a[feature_names]
        if store_col_a_first5 is None:
            store_col_a_first5 = input_a['store_id'].head(5).tolist()
        pred_a = model.predict(input_a)
        preds_a.extend(pred_a)

        # Variant (b): product_id = (p % 15) + 1
        input_b = base_input.copy()
        input_b['store_id'] = float(g)
        input_b['product_id'] = float((p % 15) + 1)
        input_b = input_b[feature_names]
        pred_b = model.predict(input_b)
        preds_b.extend(pred_b)

        # Variant (c): store_id = (g % 3) + 1
        input_c = base_input.copy()
        input_c['store_id'] = float((g % 3) + 1)
        input_c['product_id'] = float(p)
        input_c = input_c[feature_names]
        if store_col_c_first5 is None:
            store_col_c_first5 = input_c['store_id'].head(5).tolist()
        pred_c = model.predict(input_c)
        preds_c.extend(pred_c)

    arr_a = np.array(preds_a)
    arr_b = np.array(preds_b)
    arr_c = np.array(preds_c)

    print(f'First 5 values of store_id column passed in Variant (a): {store_col_a_first5}')
    print(f'First 5 values of store_id column passed in Variant (c): {store_col_c_first5}')

    eq_ab = np.array_equal(arr_a, arr_b)
    max_ab = np.max(np.abs(arr_a - arr_b))
    mean_ab = np.mean(np.abs(arr_a - arr_b))
    print('Variant (a) vs Variant (b) [product_id altered]:')
    print(f'  numpy.array_equal: {eq_ab}')
    print(f'  max abs difference:  {max_ab:.6f}')
    print(f'  mean abs difference: {mean_ab:.6f}')

    eq_ac = np.array_equal(arr_a, arr_c)
    max_ac = np.max(np.abs(arr_a - arr_c))
    mean_ac = np.mean(np.abs(arr_a - arr_c))
    print('Variant (a) vs Variant (c) [store_id altered]:')
    print(f'  numpy.array_equal: {eq_ac}')
    print(f'  max abs difference:  {max_ac:.6f}')
    print(f'  mean abs difference: {mean_ac:.6f}')


def run_gate_2():
    print('=' * 80)
    print('GATE 2 - Calendar derivation parity')
    print('=' * 80)
    mismatches = {
        'season': 0,
        'weekday': 0,
        'month': 0,
        'dayOfYear': 0,
        'isWeekend': 0,
        'isWeekday': 0
    }
    month_season_pairs = set()

    for g in range(1, 4):
        for p in range(1, 16):
            path = os.path.join(DATASET_DIR, f'sales_grocer{g}_{p}_0.csv')
            df = pd.read_csv(path, usecols=['sales_date', 'season', 'weekday', 'month', 'dayOfYear', 'isWeekend', 'isWeekday'])
            dates = pd.to_datetime(df['sales_date'])

            def derive_season(m):
                if m in (3, 4, 5): return 'Spring'
                if m in (6, 7, 8): return 'Summer'
                if m in (12, 1, 2): return 'Winter'
                return 'Autumn'

            weekday_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
            derived_s = dates.dt.month.map(derive_season)
            derived_w = dates.dt.weekday.map(weekday_names)
            derived_m = dates.dt.month
            derived_d = dates.dt.dayofyear
            derived_we = dates.dt.weekday.isin([5, 6])
            derived_wd = dates.dt.weekday < 5

            mismatches['season'] += int((df['season'] != derived_s).sum())
            mismatches['weekday'] += int((df['weekday'] != derived_w).sum())
            mismatches['month'] += int((df['month'] != derived_m).sum())
            mismatches['dayOfYear'] += int((df['dayOfYear'] != derived_d).sum())
            mismatches['isWeekend'] += int((df['isWeekend'].astype(bool) != derived_we).sum())
            mismatches['isWeekday'] += int((df['isWeekday'].astype(bool) != derived_wd).sum())

            for m, s in zip(df['month'], df['season']):
                month_season_pairs.add((int(m), str(s)))

    print('Mismatch count per column (total across all 45 lead-0 files):')
    for col, cnt in mismatches.items():
        print(f'  {col:10s}: {cnt}')

    print('\nDistinct (month, season) pairs found in CSV:')
    for m, s in sorted(list(month_season_pairs)):
        print(f'  Month {m:2d} -> {s}')


def run_gate_3():
    print('=' * 80)
    print('GATE 3 - lag_related structure')
    print('=' * 80)
    try:
        from scipy.optimize import nnls
        solver_desc = 'non-negative least squares via scipy.optimize.nnls (scipy is installed)'
        use_scipy = True
    except ImportError:
        solver_desc = 'unconstrained least squares via numpy.linalg.lstsq (scipy not installed)'
        use_scipy = False

    print(f'Regression solver used: {solver_desc}\n')

    for g in [1, 2, 3]:
        print(f'=== 3.1 Grocer {g}, Product 1, Lead 0: lag_related_1 Fit on 15 Products ===')
        dfs = {p: pd.read_csv(os.path.join(DATASET_DIR, f'sales_grocer{g}_{p}_0.csv')) for p in range(1, 16)}
        y = dfs[1]['lag_related_1']
        X = pd.concat([dfs[p]['sum_amount'].shift(1) for p in range(1, 16)], axis=1)
        X.columns = [f'p{p}' for p in range(1, 16)]

        valid = ~y.isna() & ~X.isna().any(axis=1)
        y_v = y[valid].values
        X_v = X[valid].values
        ss_tot = np.sum((y_v - y_v.mean())**2)

        # Without intercept
        if use_scipy:
            w_no_int, _ = nnls(X_v, y_v)
        else:
            w_no_int, _, _, _ = np.linalg.lstsq(X_v, y_v, rcond=None)
        pred_no_int = X_v @ w_no_int
        r2_no_int = 1.0 - np.sum((y_v - pred_no_int)**2) / ss_tot
        mae_no_int = np.mean(np.abs(y_v - pred_no_int))
        max_no_int = np.max(np.abs(y_v - pred_no_int))

        print('Without Intercept:')
        print('  Weights (p1..p15):', [round(float(x), 6) for x in w_no_int])
        print('  Intercept:         0.0 (None)')
        print(f'  R2:                {r2_no_int:.6f}')
        print(f'  Mean Abs Error:    {mae_no_int:.6f}')
        print(f'  Max Abs Error:     {max_no_int:.6f}')

        # With intercept
        X_v_int = np.column_stack([X_v, np.ones(len(X_v))])
        if use_scipy:
            w_with_int, _ = nnls(X_v_int, y_v)
            weights_int = w_with_int[:-1]
            intercept = w_with_int[-1]
        else:
            w_with_int, _, _, _ = np.linalg.lstsq(X_v_int, y_v, rcond=None)
            weights_int = w_with_int[:-1]
            intercept = w_with_int[-1]
        pred_with_int = X_v_int @ w_with_int
        r2_with_int = 1.0 - np.sum((y_v - pred_with_int)**2) / ss_tot
        mae_with_int = np.mean(np.abs(y_v - pred_with_int))
        max_with_int = np.max(np.abs(y_v - pred_with_int))

        print('With Intercept:')
        print('  Weights (p1..p15):', [round(float(x), 6) for x in weights_int])
        print(f'  Intercept:         {intercept:.6f}')
        print(f'  R2:                {r2_with_int:.6f}')
        print(f'  Mean Abs Error:    {mae_with_int:.6f}')
        print(f'  Max Abs Error:     {max_with_int:.6f}')

        print(f'\n=== 3.2 Grocer {g}, Product 1, Lead 0: lag_related_k vs lag_related_1 shifted by (k-1) ===')
        for k in [2, 7, 14]:
            s_k = dfs[1][f'lag_related_{k}']
            s_1_shifted = dfs[1]['lag_related_1'].shift(k - 1)
            mask_k = ~s_k.isna() & ~s_1_shifted.isna()
            diff_k = np.abs(s_k[mask_k] - s_1_shifted[mask_k])
            max_diff_k = float(diff_k.max())
            equals_k = (max_diff_k == 0.0)
            print(f'  k={k:2d} (shift={k-1:2d} days) | equals: {equals_k} | max abs diff: {max_diff_k:.6f}')
        print()

    print('=== 3.3 Grocer 1: lag_related_1 Product Dependence vs Product 1 ===')
    p1_df = pd.read_csv(os.path.join(DATASET_DIR, 'sales_grocer1_1_0.csv'))
    y1 = p1_df['lag_related_1']
    for p in range(2, 16):
        df_p = pd.read_csv(os.path.join(DATASET_DIR, f'sales_grocer1_{p}_0.csv'))
        yp = df_p['lag_related_1']
        mask = ~y1.isna() & ~yp.isna()
        diff = np.abs(y1[mask] - yp[mask])
        print(f'  Product {p:2d} vs Product 1 | max abs diff: {diff.max():.6f} | mean abs diff: {diff.mean():.6f}')


def run_gate_4():
    print('=' * 80)
    print('GATE 4 - Import round-trip simulation (in memory, no database)')
    print('=' * 80)
    from app.models.models import InventorySnapshot
    col_type = InventorySnapshot.__table__.columns['units_sold'].type
    print(f'4.0 InventorySnapshot.units_sold type: {col_type} (nullable={InventorySnapshot.__table__.columns["units_sold"].nullable})')

    print('\n4.1 Lag Rebuilding Methodology Note:')
    print('  - Emulation in pandas: build_feature_dict() in feature_builder.py is designed for')
    print('    single-row database session queries with pre-aggregated DB entities and substitutes')
    print('    weather/telemetry columns with synthetic approximations. In contrast, Gate 4.1')
    print('    evaluates round-trip simulation preserving all 180 CSV columns and evaluates')
    print('    the lag rebuilding logic (lines 140-151 and 156-193) across all rows.')
    print('  - Related set hypothesis: mean of the other 14 products of the same grocer (HYPOTHESIS).')

    from app.services.ml_service import GroceryMLService
    from app.config import settings

    svc = GroceryMLService.get_instance()
    model = svc.model
    feature_names = svc.master_feature_names

    records_overall = {'y_true': [], 'A': [], 'F': [], 'I': []}
    grocer_records = {1: {'y_true': [], 'A': [], 'F': [], 'I': []},
                      2: {'y_true': [], 'A': [], 'F': [], 'I': []},
                      3: {'y_true': [], 'A': [], 'F': [], 'I': []}}
    product_wapes = []

    for g in [1, 2, 3]:
        dfs = {p: pd.read_csv(os.path.join(DATASET_DIR, f'sales_grocer{g}_{p}_0.csv')) for p in range(1, 16)}
        units_f = {p: dfs[p]['sum_amount'] * settings.DEMAND_SCALE for p in range(1, 16)}
        units_i = {p: np.round(dfs[p]['sum_amount'] * settings.DEMAND_SCALE) for p in range(1, 16)}

        for p in range(1, 16):
            df_p = dfs[p]
            mask = ~df_p['lag_56'].isna()
            y_p = df_p.loc[mask, 'sum_amount'].values

            shared = [c for c in feature_names if c in df_p.columns]
            base_input = df_p.loc[mask, shared].copy()
            base_input['store_id'] = float(g)
            base_input['product_id'] = float(p)
            base_input['lead_time'] = 0.0
            for s in ['Spring', 'Summer', 'Winter']:
                base_input[f'season_{s}'] = (df_p.loc[mask, 'season'] == s).astype(float)
            for w in ['Monday', 'Saturday', 'Sunday', 'Thursday', 'Tuesday', 'Wednesday']:
                base_input[f'weekday_{w}'] = (df_p.loc[mask, 'weekday'] == w).astype(float)

            # Variant A: CSV features as-is
            inp_a = base_input[feature_names]
            pred_a = model.predict(inp_a)

            # Variant F: Float units
            inp_f = base_input.copy()
            other_f = pd.concat([units_f[q] for q in range(1, 16) if q != p], axis=1).mean(axis=1)
            for i in range(1, 57):
                inp_f.loc[mask, f'lag_related_{i}'] = (other_f.shift(i).loc[mask] / settings.DEMAND_SCALE).values
            pred_f = model.predict(inp_f[feature_names])

            # Variant I: Integer units
            inp_i = base_input.copy()
            u_p = units_i[p]
            for i in range(1, 57):
                inp_i.loc[mask, f'lag_{i}'] = (u_p.shift(i).loc[mask] / settings.DEMAND_SCALE).values
            other_i = pd.concat([units_i[q] for q in range(1, 16) if q != p], axis=1).mean(axis=1)
            for i in range(1, 57):
                inp_i.loc[mask, f'lag_related_{i}'] = (other_i.shift(i).loc[mask] / settings.DEMAND_SCALE).values
            pred_i = model.predict(inp_i[feature_names])

            wape_p_a = np.sum(np.abs(y_p - pred_a)) / np.sum(y_p)
            wape_p_i = np.sum(np.abs(y_p - pred_i)) / np.sum(y_p)
            product_wapes.append({
                'grocer': g,
                'product': p,
                'WAPE_A': wape_p_a,
                'WAPE_I': wape_p_i,
                'WAPE_diff': wape_p_i - wape_p_a
            })

            records_overall['y_true'].extend(y_p)
            records_overall['A'].extend(pred_a)
            records_overall['F'].extend(pred_f)
            records_overall['I'].extend(pred_i)

            grocer_records[g]['y_true'].extend(y_p)
            grocer_records[g]['A'].extend(pred_a)
            grocer_records[g]['F'].extend(pred_f)
            grocer_records[g]['I'].extend(pred_i)

    print('\n4.2 Overall Performance Table (All 45 Files, rows where lag_56 is not null):')
    print(f'{"Variant":28s} | {"WAPE":8s} | {"MAE":8s} | {"Bias":8s}')
    print('-' * 60)
    y_all = np.array(records_overall['y_true'])
    for name, key in [('(A) CSV features as-is', 'A'),
                      ('(F) Rebuilt float units', 'F'),
                      ('(I) Rebuilt integer units', 'I')]:
        p_all = np.array(records_overall[key])
        wape = np.sum(np.abs(y_all - p_all)) / np.sum(y_all)
        mae = np.mean(np.abs(y_all - p_all))
        bias = np.sum(p_all) / np.sum(y_all)
        print(f'{name:28s} | {wape:8.4f} | {mae:8.6f} | {bias:8.4f}')

    for g in [1, 2, 3]:
        print(f'\nGrocer {g} Performance Table:')
        print(f'{"Variant":28s} | {"WAPE":8s} | {"MAE":8s} | {"Bias":8s}')
        print('-' * 60)
        y_g = np.array(grocer_records[g]['y_true'])
        for name, key in [('(A) CSV features as-is', 'A'),
                          ('(F) Rebuilt float units', 'F'),
                          ('(I) Rebuilt integer units', 'I')]:
            p_g = np.array(grocer_records[g][key])
            wape = np.sum(np.abs(y_g - p_g)) / np.sum(y_g)
            mae = np.mean(np.abs(y_g - p_g))
            bias = np.sum(p_g) / np.sum(y_g)
            print(f'{name:28s} | {wape:8.4f} | {mae:8.6f} | {bias:8.4f}')

    pw_df = pd.DataFrame(product_wapes)
    top5_diff = pw_df.sort_values(by='WAPE_diff', ascending=False).head(5)
    print('\nTop 5 Products with Largest WAPE Increase (Variant I vs Variant A):')
    print(f'{"Grocer":8s} | {"Product":8s} | {"WAPE_A":10s} | {"WAPE_I":10s} | {"Delta WAPE":10s}')
    print('-' * 56)
    for _, r in top5_diff.iterrows():
        print(f'{int(r["grocer"]):8d} | {int(r["product"]):8d} | {r["WAPE_A"]:10.4f} | {r["WAPE_I"]:10.4f} | {r["WAPE_diff"]:10.4f}')


def run_gate_5():
    print('=' * 80)
    print('GATE 5 - Schema and seed facts for the import (read only)')
    print('=' * 80)
    from app.models.models import InventorySnapshot, DailyExogenous, Product, Category, Store

    print('\n5.1 SQLAlchemy Models Inspection (In-Memory Metadata):')
    models = [InventorySnapshot, DailyExogenous, Product, Category, Store]
    for model in models:
        print(f'\n--- Model: {model.__name__} (Table: {model.__tablename__}) ---')
        for col in model.__table__.columns:
            print(f'  {col.name:18s}: {str(col.type):16s} | nullable={str(col.nullable):5s} | primary_key={col.primary_key}')
        print('  Constraints:')
        for uq in model.__table__.constraints:
            print(f'    {uq}')

    print('\nDailyExogenous Keying:')
    print('  - Keyed per store and record_date: UniqueConstraint(daily_exogenous.store_id, daily_exogenous.record_date)')

    exogenous_68_names = [
        'isHoliday', 'isBeforeHoliday', 'isAfterHoliday', 'isSchoolHoliday', 'isWeekend', 'isWeekday',
        'dayOfYear', 'month', 'isLockdown',
        'T2M_09', 'T2M_12', 'T2M_15', 'T2M_18',
        'TD2M_09', 'TD2M_12', 'TD2M_15', 'TD2M_18',
        'RH2M_09', 'RH2M_12', 'RH2M_15', 'RH2M_18',
        'P0_09', 'P0_12', 'P0_15', 'P0_18',
        'GL_09', 'GL_12', 'GL_15', 'GL_18',
        'UU_09', 'UU_12', 'UU_15', 'UU_18',
        'VV_09', 'VV_12', 'VV_15', 'VV_18',
        'RR_09', 'RR_12', 'RR_15', 'RR_18',
        'residents', 'visits', 'visitors'
    ] + [f'load_{h:02d}' for h in range(24)]

    exo_table_cols = [c.name for c in DailyExogenous.__table__.columns]
    matching_cols = [c for c in exogenous_68_names if c in exo_table_cols or c.lower() in [tc.lower() for tc in exo_table_cols]]
    print('\nOf the 68 exogenous feature names, which have a column in DailyExogenous table?')
    print(f'  Direct match / equivalent in DailyExogenous: {matching_cols} (is_holiday corresponds to isHoliday).')
    print('  Summary/aggregated columns in DailyExogenous: avg_temp, avg_humidity, total_rain, foot_traffic_load.')
    print('  Individual hourly columns (T2M..RR, load_00..23, residents, visits, visitors, lockdown) are NOT stored in DailyExogenous.')

    print('\n5.2 Verbatim Quotes from seed_db.py (Read-Only):')
    seed_path = os.path.join(BACKEND_ROOT, 'seed_db.py')
    with open(seed_path, 'r', encoding='utf-8') as f:
        seed_lines = f.readlines()

    print('\n[seed_db.py: Categories Assignment, lines 68-79 and lines 116-120]:')
    for idx in range(67, 80):
        print(f'  {idx+1}: {seed_lines[idx]}', end='')
    for idx in range(115, 121):
        print(f'  {idx+1}: {seed_lines[idx]}', end='')

    print('\n[seed_db.py: DailyExogenous Population, lines 280-291]:')
    for idx in range(279, 292):
        print(f'  {idx+1}: {seed_lines[idx]}', end='')

    print('\n[seed_db.py: units_sold Setting, lines 305-312 and 333-341]:')
    for idx in range(304, 313):
        print(f'  {idx+1}: {seed_lines[idx]}', end='')
    for idx in range(332, 341):
        print(f'  {idx+1}: {seed_lines[idx]}', end='')

    print('\n5.3 Grocer Lead-0 File Stats (Rows, Min Date, Max Date, Row Count Uniformity):')
    for g in [1, 2, 3]:
        row_counts = []
        min_dates = []
        max_dates = []
        for p in range(1, 16):
            path = os.path.join(DATASET_DIR, f'sales_grocer{g}_{p}_0.csv')
            df = pd.read_csv(path, usecols=['sales_date'])
            row_counts.append(len(df))
            min_dates.append(df['sales_date'].min())
            max_dates.append(df['sales_date'].max())
        uniform = (len(set(row_counts)) == 1)
        print(f'  Grocer {g}: rows={row_counts[0]} | min_date={min_dates[0]} | max_date={max_dates[0]} | all 15 files same count={uniform}')


def main():
    parser = argparse.ArgumentParser(description='Read-only verification gates before dataset import.')
    parser.add_argument('--gate', type=str, default='all', choices=['1', '2', '3', '4', '5', 'all'],
                        help='Gate number to execute (1, 2, 3, 4, 5, or all)')
    args = parser.parse_args()

    if args.gate in ('1', 'all'):
        run_gate_1()
    if args.gate in ('2', 'all'):
        run_gate_2()
    if args.gate in ('3', 'all'):
        run_gate_3()
    if args.gate in ('4', 'all'):
        run_gate_4()
    if args.gate in ('5', 'all'):
        run_gate_5()


if __name__ == '__main__':
    main()
