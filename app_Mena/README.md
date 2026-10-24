# ZeroWaste Grocer 🥦📉

ZeroWaste Grocer is an intelligent, grocery inventory management and AI-driven perishable replenishment mobile application designed to eliminate grocery food waste, optimize margins, and automate dynamic markdown decisions.

Built with **Flutter**, **Riverpod**, **Clean Architecture (feature-first)**, and backed by a high-performance **FastAPI** service embedding a 192-feature **LightGBM** demand inference engine, **Newsvendor Critical Fractile** replenishment optimizer, and **TreeSHAP Explainable AI (XAI)**.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Flutter SDK**: 3.19.0 or newer
- **Python**: 3.10+ with virtual environment
- **Android Emulator / Physical Device / Windows Desktop**

---

### 2. Running the Backend Service

The backend is built with FastAPI and SQLite.

```powershell
# Navigate to backend directory
cd f:\Development\Projects\Mobile-Apps\backend

# Activate the virtual environment
.\.venv\Scripts\activate

# Start the Uvicorn development server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> **API Documentation**: Once running, open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser for the interactive Swagger UI.

---

### 3. Running the Flutter App

```powershell
# Navigate to Flutter app directory
cd f:\Development\Projects\Mobile-Apps\app_Mena

# Install dependencies
flutter pub get

# Launch the app
flutter run
```

* **Android Emulator**: Automatically routes HTTP requests to `http://10.0.2.2:8000/api/v1`.
* **Windows / Web / iOS**: Automatically routes HTTP requests to `http://127.0.0.1:8000/api/v1`.

---

## 🔑 Demo Credentials

Reviewers and examiners can sign in with:

| Field | Value |
| :--- | :--- |
| **Email** | `manager@zerowaste.com` |
| **Password** | `password123` |
| **Role** | Store Manager |

> ⚡ **Quick Demo Login**: You can also simply click the **"Quick Demo Login"** button on the login screen to automatically fill credentials and log in with a single tap.

---

## 🏛 Architecture Overview

The codebase strictly adheres to **Clean Architecture** organized with a **feature-first** structure:

```text
lib/
├── core/
│   ├── config/          # AppConfig (mock toggle, dynamic base URLs, timeouts)
│   ├── network/         # Shared Dio client with Bearer token interceptor and logging
│   ├── offline/         # Hive offline queue service for approvals & audits
│   ├── router/          # GoRouter with bottom navigation shell & startup sync
│   └── theme/           # AppColors (Forest Green, Eco Safe, Warning, Critical)
└── features/
    ├── auth/            # Staff authentication & multi-store switcher (UC-01)
    ├── dashboard/       # Real-time sustainability & exposure KPI cards
    ├── catalog/         # Perishable inventory catalog, category filtering, search, audit (UC-02, UC-03)
    ├── reorder/         # AI Replenishment recommendations, overrides, TreeSHAP XAI (UC-04, UC-05)
    ├── alerts/          # Spoilage markdown alert engine & actions (UC-06, UC-07)
    └── analytics/       # FL Chart visual analytics (Sales series, Waste curves, Categories) (UC-08)
```

Each feature is partitioned into three layers:
1. **Domain**: Pure Dart models and abstract repository contracts (no Flutter/Dio imports).
2. **Data**: DTO models with `fromJson`/`toJson`, remote data sources (via `Dio`), and remote/mock repository implementations.
3. **Presentation**: Riverpod state providers, screens, and reusable widgets.

---

## 📱 Use Cases Implemented & Verified

- **UC-01: Multi-Store Switcher**: Seamlessly switch between Store 1, Store 2, and Store 3 from the top AppBar dropdown. Automatically refreshes inventory, alerts, recommendations, and KPIs.
- **UC-02: Perishable Product Catalog**: Fast filtering by department (*Produce*, *Dairy*, *Bakery*, *Butchery*), 300ms debounced search, expiry urgency sort toggle, and batch expiration tracking.
- **UC-03: Closing Inventory Audit**: Rapid end-of-day count submission for on-hand and spoiled inventory, with optimistic offline buffering when disconnected.
- **UC-04 & UC-05: AI Replenishment & Explainable AI (TreeSHAP)**: Single-tap order approval, numeric stepper quantity override with required reason codes, "Approve All" action, and expandable **"Why this amount?"** breakdown detailing LightGBM forecast, safety buffer, and top feature drivers.
- **UC-06 & UC-07: Dynamic Spoilage Alerts**: Real-time markdown alerts for perishable batches nearing expiration (≤ 2 days), with one-tap 25%/40% markdown acceptance and dismissal.
- **UC-08: Sustainability & Demand Analytics**: Interactive charts built with `fl_chart`:
  1. *Actual vs Predicted Sales* (30-day dual series with tooltips)
  2. *Cumulative Waste Reduction* (running total of avoided waste)
  3. *Waste by Category* (departmental waste breakdown)

---

## 💾 Offline Queue & Resilience

- **Hive Storage**: Pending approvals (`offline_approvals_box`) and closing audits (`offline_audits_box`) are persisted locally if a network timeout or connection failure occurs.
- **Optimistic UI**: Approvals succeed immediately with feedback (`"Buffered offline for synchronization"`).
- **Auto-Sync**: When the app launches or connection is restored, pending requests are automatically flushed to the live backend, displaying a confirmation banner (`"Offline changes synced to server"`).

---

## 🧪 Testing & Verification

Run static analysis:
```bash
flutter analyze
# Output: No issues found!
```

Run test suite:
```bash
flutter test
# Output: All tests passed! (6 passed)
```
