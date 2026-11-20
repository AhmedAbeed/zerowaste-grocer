# ZeroWaste Grocer 🥦🛒

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Client-Flutter_3.24+-02569B.svg?logo=flutter&logoColor=white)](https://flutter.dev)
[![LightGBM](https://img.shields.io/badge/ML-LightGBM_Quantile-FFA000.svg)](https://lightgbm.readthedocs.io/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.14-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![WCAG 2.1 AA](https://img.shields.io/badge/Accessibility-WCAG_2.1_AA_Compliant-success.svg)](https://www.w3.org/WAI/WCAG21/quickref/)

**ZeroWaste Grocer** is an enterprise AI-powered retail grocery inventory management and waste-reduction platform. It combines Machine Learning demand forecasting (**LightGBM quantile regression** with 194 engineered features), dynamic expiration markdown execution, Explainable AI (**TreeSHAP**) replenishment recommendations, and physical closing stock audits to eliminate perishable food waste while safeguarding grocery retail profit margins.

---

## ⚡ Quickstart Guide (Run in 3 Minutes)

### Step 1: Run the Backend API

1. Open a terminal in the `backend/` folder:
```bash
cd backend
```

2. Create and activate a Python virtual environment:
```bash
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Seed the SQLite database with realistic stores, products, batches, and users:
```bash
python seed_db.py
```

5. Launch the FastAPI server:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
> 🌐 **Interactive API Documentation (Swagger)**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.

---

### Step 2: Run the Flutter Client

1. Open a second terminal in the `app_Mena/` folder:
```bash
cd app_Mena
```

2. Fetch Flutter packages:
```bash
flutter pub get
```

3. Choose your target platform:

#### Option A: Run on Google Chrome (Web)
```bash
flutter run -d chrome
```

#### Option B: Run on Android Emulator
```bash
# If using an Android Emulator, forward the backend port:
adb reverse tcp:8000 tcp:8000

# Run the app:
flutter run
```

#### Option C: Run on Windows Desktop
```bash
flutter run -d windows
```

---

## 🔑 Demo User Accounts & Roles

The system comes pre-seeded with 4 distinct roles enforcing symmetric frontend/backend **Role-Based Access Control (RBAC)**:

| Role | Email | Password | Assigned Branch | Accessible Views & Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Inventory Clerk** | `clerk@zerowaste.com` | `clerk123` | Store #1 | **Catalog only** + **Add Shipment** button. Can receive and register incoming perishable batches. Prevented from auditing or approvals. |
| **Inventory Auditor** | `auditor@zerowaste.com` | `auditor123` | Store #1 | **Catalog only** + **Audit** button. Rapid end-of-day stock count and spoilage reporting. Prevented from shipments or approvals. |
| **Store Manager** | `manager@zerowaste.com` | `password123` | Store #1 (Metro Downtown) | **5 Navigation Tabs**: Dashboard (KPIs), Catalog (read-only), Reorder (Approve/Override), Alerts (Markdown/Dismiss), Analytics + Broadcasts. |
| **System Admin** | `admin@zerowaste.com` | `admin123` | All Stores (Enterprise) | **4 Navigation Tabs**: Dashboard, Catalog, Enterprise Stores (Create Branch & Assign Manager), Analytics + Enterprise Broadcast Dispatch. |

> ⚡ **Single-Tap Demo Login**: On the mobile login screen, tap the **"Quick Demo Login"** button to automatically log in as the Store Manager.

---

## 🧠 Machine Learning & Forecasting Architecture

### 1. 194-Feature Pipeline (`feature_builder.py`)
The prediction engine extracts 194 features per product for any evaluated forecast date:
- **Lags**: 1 to 28 days of historical sales.
- **Rolling Means**: 7-day, 14-day, and 28-day moving averages strictly calculated with `shift(1)` to prevent target-day leakage.
- **Rolling Volatilities**: Moving standard deviations and coefficient of variation.
- **Exogenous Telemetry**: Ambient temperature, foot traffic, precipitation, holidays, promotions, and day-of-week seasonality.
- **Pricing & Margin**: Unit price, unit cost, price elasticity, and discount percentage.

### 2. Quantile Loss Regression (`LightGBM`)
- Optimizes pinball loss at the 85th percentile ($\alpha = 0.85$) to penalize out-of-stock events while curbing perishable excess.
- Regularized using L2 penalty (`lambda_l2: 1.5`, `min_child_samples: 25`) to resist overfitting on small retail histories.

### 3. Explainable AI (TreeSHAP)
- Every automated replenishment recommendation generates a human-readable XAI breakdown.
- Managers can tap **"Why this amount?"** on any reorder card to inspect top positive and negative feature drivers.

### 4. Telemetry Logging without Live Retraining
- The `/ai/ultra/feedback` endpoint records operational discrepancies to the `ModelFeedback` table for performance evaluation without unsafe online retraining in memory.

---

## 📱 Feature Highlights

- **Dynamic Spoilage Markdown Engine**:
  - Automatically identifies batches within $\le 2$ days of expiration.
  - Suggests algorithmic discounts (25% to 40%) to accelerate sell-through before disposal.
  - Applying markdowns immediately updates batch retail pricing.

- **Offline Queue & Optimistic UI**:
  - Built with Hive key-value persistence.
  - When connection is lost, manager order approvals and auditor counts are safely buffered offline in local storage.
  - Automatically flushed to the backend server with confirmation banners when reconnected.

- **Enterprise Multi-Branch Isolation (IDOR-Protected)**:
  - Strict branch isolation ensures store managers, clerks, and auditors can only inspect and modify their designated store.
  - Enterprise Admin can oversee all stores, create new branches, and dispatch global announcements.

- **Accessible Dual Theme (Light & Dark Mode)**:
  - Tested and verified for **WCAG 2.1 AA** color contrast ratios across all surfaces, text colors, and chart lines ($\ge 14.8:1$ primary text, $\ge 5.3:1$ charts).
  - Theme mode is instantly toggled from the top AppBar and preserved across app restarts.

---

## 🏛 Clean Architecture & Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # FastAPI REST route controllers (auth, inventory, replenishment, admin...)
│   │   ├── core/              # Security (JWT, bcrypt, RBAC dependencies, branch isolation)
│   │   ├── db/                # SQLAlchemy session, engine, and base
│   │   ├── models/            # Database schema models (Store, Product, Batch, Order, User...)
│   │   ├── schemas/           # Pydantic v2 validation contracts
│   │   └── services/          # Business logic & ML (feature builder, lightgbm, reorder, sigma)
│   ├── ml_artifacts/          # Production trained model weights & 194-feature master joblib
│   ├── main.py                # FastAPI entry point & CORS configuration
│   ├── seed_db.py             # Deterministic database seeding script
│   ├── test_fixes.py          # Automated verification test suite for RBAC & validations
│   └── test_real_data.py      # Real retail dataset model accuracy verification
│
├── app_Mena/
│   ├── lib/
│   │   ├── core/              # Network (Dio client), Router (GoRouter), Theme, Offline Queue
│   │   └── features/
│   │       ├── auth/          # Login screen, user model, auth providers
│   │       ├── dashboard/     # Store sustainability KPIs, Units at Risk cards
│   │       ├── catalog/       # Product catalog, category chips, batch bottom sheet
│   │       ├── reorder/       # Replenishment recommendations, override steppers, XAI
│   │       ├── alerts/        # Markdown alerts, urgency badges, dismiss actions
│   │       ├── analytics/     # FlChart interactive visual charts
│   │       ├── broadcasts/    # Enterprise announcements view
│   │       └── admin/         # Enterprise branch management screen
│   └── test/                  # Unit and widget test suite (25 automated tests)
```

---

## 🧪 Testing & Verification Commands

All automated tests across the backend and frontend client can be verified with single commands:

### Backend Tests
```bash
cd backend

# 1. Run targeted RBAC, branch isolation, and batch validation tests:
python test_fixes.py
# Output: ALL TARGETED FIX TESTS PASSED SUCCESSFULLY!

# 2. Run real Zenodo retail dataset ML accuracy & forecasting evaluation:
python test_real_data.py
# Output: PASSED (WAPE: 52.12%, MAE: 0.078762, Bias: 0.7798)
```

### Flutter Static Analysis & Widget Tests
```bash
cd app_Mena

# 1. Run static code analysis:
flutter analyze
# Output: No issues found!

# 2. Run all unit and widget tests:
flutter test
# Output: All 25 tests passed!
```

---

## 🔄 Resetting the Database

If test data is entered during demonstration, reset both database environments back to clean seed with:

```bash
cd backend
python seed_db.py
```

---

## 📄 License & Attribution

Distributed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)** license.
