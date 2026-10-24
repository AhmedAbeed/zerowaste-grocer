# ZeroWaste Grocer: Comprehensive Technical & System Engineering Report

**AI-Driven Perishable Inventory & Food Waste Minimization System**  
*Full Stack Architectural Blueprint, Machine Learning Pipeline, Codebase Catalog, and Verification Audit*

---

## 1. Executive Summary & System Purpose

Retail grocery stores suffer from systemic financial and environmental losses in perishable categories (fresh produce, dairy, bakery, and butchery). Traditional replenishment depends on static heuristics, blunt minimum/maximum inventory rules, or subjective human intuition. This structural friction causes:
1. **Severe Food Spoilage & Financial Exposure:** Over-ordering leads to expired inventory that must be discarded to landfills, generating Scope 3 greenhouse gas ($CO_2e$) emissions and direct capital loss.
2. **Costly Stockouts:** Under-ordering leads to empty shelves, frustrated shoppers, and forfeited gross margin.

**ZeroWaste Grocer** eliminates this inefficiency through a synchronized, production-grade **Full-Stack Decision Support System**:
* **Mobile Application (Flutter 3.x):** An intuitive, eco-themed operational client for store managers, featuring multi-branch switching, real-time KPI monitoring, perishable inventory audits, Explainable AI reorder recommendations, automated spoilage alerts, and sustainability analytics.
* **Backend Inference & Orchestration Engine (FastAPI & SQLite):** An in-memory machine learning server that loads a pre-trained LightGBM Regressor, constructs an exact 192-feature matrix from historical point-of-sale data and exogenous climate/traffic telemetry, calculates mathematically optimal order buffers via the **Newsvendor Critical Fractile Model**, and exposes 12 production-ready RESTful endpoints.

---

## 2. Execution Environment: Local vs. Cloud

The entire system is engineered to run **100% locally and self-contained on localhost/LAN** without reliance on external paid cloud services, third-party brokers, or remote microservices:

* **Backend Execution:** Runs locally via Python's asynchronous server `uvicorn` listening on port `8000` (`http://127.0.0.1:8000` or `http://0.0.0.0:8000`).
* **Database Management:** Uses an embedded **SQLite database (`zerowaste.db`)** accessed through SQLAlchemy 2.0 ORM, guaranteeing zero-configuration deployment across developer machines.
* **Mobile Communication Topology:**
  * **Android Emulator:** Reaches the local host machine using the virtual router alias `http://10.0.2.2:8000/api/v1`.
  * **Windows Desktop / Chrome Web:** Reaches the server directly via `http://127.0.0.1:8000/api/v1`.
  * **Physical Device (via Wi-Fi LAN):** Configured by pointing the client to the host PC's local network IP address (e.g., `http://192.168.1.X:8000/api/v1`).
* **Offline Resilience:** The Flutter mobile application incorporates a local **Hive NoSQL database** acting as a persistent write-through queue. If network connectivity drops, stock audits and reorder approvals are buffered locally and automatically synchronized upon app restart or reconnection.

---

## 3. Complete Technology Stack & Tools

### Mobile Frontend Stack (Flutter)
| Technology / Package | Version | Architectural Responsibility |
|---|---|---|
| **Flutter SDK** | `^3.11.0` | Cross-platform UI toolkit targeting Android, iOS, Windows, and Web. |
| **flutter_riverpod** | `^2.6.1` | Reactive, unidirectional state management and dependency injection. |
| **go_router** | `^17.5.0` | Declarative routing, navigation auth guards, and `StatefulShellRoute`. |
| **dio** | `^5.11.1` | Asynchronous HTTP networking client with automated JWT bearer interceptors. |
| **hive / hive_flutter** | `^2.2.3` / `^1.1.0` | High-throughput local key-value storage for offline action queueing. |
| **fl_chart** | `^1.2.0` | Hardware-accelerated data visualization for trends and category breakdowns. |
| **intl** | `^0.20.3` | Date/time localization and calendar formatters. |

### Backend & Machine Learning Stack (Python)
| Technology / Package | Version | Architectural Responsibility |
|---|---|---|
| **Python** | `3.10+` | Primary server runtime. |
| **FastAPI** | `^0.110.0` | High-performance asynchronous REST API framework with automated OpenAPI docs. |
| **uvicorn[standard]** | `^0.29.0` | ASGI production web server. |
| **SQLAlchemy** | `^2.0.0` | Declarative relational Object-Relational Mapping (ORM) and session management. |
| **SQLite3** | `3.x` | Embedded relational database engine. |
| **Pydantic v2** | `^2.6.0` | Strict data validation, schema serialization, and API Contract enforcement. |
| **LightGBM** | `^4.0.0` | Pre-trained gradient boosted decision tree regressor (`production_model.joblib`). |
| **scikit-learn** | `^1.3.0` | Model serialization utilities and regression preprocessing. |
| **scipy** | `^1.11.0` | Statistical distributions; computes inverse normal CDF (`norm.ppf`) for Newsvendor. |
| **pandas / numpy** | `^2.0.0` / `^1.24.0` | 192-feature input matrix construction, time-series lag slicing, and vector math. |
| **pyjwt / passlib** | `^2.8.0` / `^1.7.4` | HMAC-SHA256 JWT access token generation and authorization verification. |

---

## 4. Machine Learning & Optimization Engine Deep Dive

### 4.1 The 192-Feature Matrix Contract
The pre-trained LightGBM model requires a numerical input matrix of **exactly 192 columns** in a strict categorical and chronological sequence serialized in `master_feature_names.joblib`:

1. **Features [0–8] (Temporal & Calendar):** `isHoliday`, `isBeforeHoliday`, `isAfterHoliday`, `isSchoolHoliday`, `isWeekend`, `isWeekday`, `dayOfYear`, `month`, `isLockdown`.
2. **Features [9–40] (ERA5 Climate):** Hourly measurements for 09:00, 12:00, 15:00, and 18:00 across ambient temperature (`T2M`), dew point (`TD2M`), relative humidity (`RH2M`), surface pressure (`P0`), solar global radiation (`GL`), wind vectors (`UU`, `VV`), and liquid precipitation (`RR`).
3. **Features [41–43] (Cellular Foot Traffic Density):** `residents`, `visits`, `visitors`.
4. **Features [44–67] (Hourly Pedestrian Activity):** Continuous diurnal distribution curve (`load_00` to `load_23`).
5. **Features [68–123] (Direct Historical Sales Lags):** Daily unit sales history for the preceding 56 days (`lag_1` to `lag_56`), normalized by `DEMAND_SCALE`.
6. **Features [124–179] (Related Category Historical Sales Lags):** 56-day cross-elasticity demand indicators aggregated across substitute/complementary products in the same grocery department (`lag_related_1` to `lag_related_56`).
7. **Features [180–182] (Core Entity Keys):** `store_id`, `product_id`, `lead_time`.
8. **Features [183–191] (One-Hot Encodings):** Seasonal indicators (`season_Spring`, `season_Summer`, `season_Winter`) and day-of-week indicators (`weekday_Monday` through `weekday_Wednesday`, `weekday_Thursday`, `weekday_Saturday`, `weekday_Sunday`).

### 4.2 Target Scaling Constant (`DEMAND_SCALE`)
Because the pre-trained LightGBM model was normalized on a compressed continuous distribution (producing baseline values around $\approx 0.088$), the backend incorporates an adjustable scaling constant:
$$\text{DEMAND\_SCALE} = 250.0$$
* **Inference Post-Processing:** $\text{predicted\_units} = \max(1, \text{round}(\hat{y} \times \text{DEMAND\_SCALE}))$.
* **Feature Construction Pre-Processing:** $\text{lag\_}i = \frac{\text{snapshot.units\_sold}}{\text{DEMAND\_SCALE}}$.

### 4.3 Operations Research: Newsvendor Critical Fractile Model
Raw demand prediction alone does not solve inventory management because demand is inherently stochastic. ZeroWaste Grocer evaluates financial risk trade-offs using the Newsvendor optimization algorithm:

1. **Underage Cost ($Cu$):** The opportunity cost of under-ordering (lost gross margin):
   $$Cu = \text{unit\_price} - \text{unit\_cost}$$
2. **Overage Cost ($Co$):** The direct loss of over-ordering perishable stock that expires:
   $$\text{salvage\_value} = \text{unit\_cost} \times 0.20 \quad (\text{20\% salvage assumption})$$
   $$Co = \text{unit\_cost} - \text{salvage\_value}$$
3. **Critical Fractile ($CF$):** The optimal service level target:
   $$CF = \frac{Cu}{Cu + Co} \in [0.01, 0.99]$$
4. **Safety Factor ($k$):** The standard normal deviate for the target service level:
   $$k = \Phi^{-1}(CF) = \text{scipy.stats.norm.ppf}(CF)$$
5. **Demand Volatility Buffer:**
   $$\sigma_e = \max(1.0, \text{predicted\_units} \times 0.15)$$
   $$\text{optimal\_buffer} = \max(\text{safety\_stock}, \text{round}(k \times \sigma_e))$$
6. **Final Recommended Order Quantity:**
   $$\text{Order} = \max(0, \text{predicted\_units} + \text{optimal\_buffer} - \text{current\_stock})$$

### 4.4 Explainable AI (TreeSHAP) Attribution
Rather than behaving as a black-box model, the system queries the LightGBM booster's native Shapley values via `pred_contrib=True`. It extracts the top 3 contributing features by absolute magnitude, maps technical column keys to plain-English retail drivers (e.g., `isWeekend` $\rightarrow$ *"Weekend Foot-Traffic Surge"*), and computes relative impact percentages summing to $100.0\%$.

---

## 5. Complete Codebase Directory & File Trees

### 5.1 Backend Service Directory (`backend/`)

```text
f:/Development/Projects/Mobile-Apps/backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py                  # Consolidated v1 API router
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── alerts.py                # Spoilage alerts & markdown triggers
│   │           ├── analytics.py             # Waste metrics, sales series, category waste
│   │           ├── auth.py                  # JWT staff login & token issuing
│   │           ├── inventory.py             # Store inventory, batches, closing audits
│   │           ├── prediction.py            # Direct ML demand inference endpoint
│   │           ├── replenishment.py         # AI replenishment recommendations & approvals
│   │           └── stores.py                # Retail store branch management
│   ├── core/
│   │   ├── __init__.py
│   │   └── security.py                      # HMAC-SHA256 JWT auth & user dependencies
│   ├── db/
│   │   ├── __init__.py                      # Database session & base exports
│   │   ├── base.py                          # SQLAlchemy DeclarativeBase
│   │   └── session.py                       # SQLite engine connection & get_db dependency
│   ├── models/
│   │   ├── __init__.py                      # Consolidated ORM exports
│   │   └── models.py                        # 9 relational database schema models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── api_schemas.py                   # Pydantic v2 schemas for all 12 REST endpoints
│   │   └── ml_schemas.py                    # Low-level ML prediction schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── alert_service.py                 # Dynamic spoilage evaluation engine
│   │   ├── feature_builder.py               # Strict 192-feature matrix builder pipeline
│   │   ├── ml_service.py                    # LightGBM singleton & TreeSHAP driver extractor
│   │   └── reorder_service.py               # Newsvendor Critical Fractile replenishment engine
│   ├── __init__.py
│   └── config.py                            # Settings, DEMAND_SCALE, and artifact paths
├── ml_artifacts/
│   ├── master_feature_names.joblib          # Ordered list of 192 feature column names
│   └── production_model.joblib              # Champion LightGBM regressor artifact (2.1 MB)
├── main.py                                  # FastAPI application initialization & CORS
├── requirements.txt                         # Production backend dependencies
├── seed_db.py                               # Database initializer & 60-day historical data seeder
├── test_ml.py                               # Level B1 verification test script
├── test_b3.py                               # Level B3 mathematical verification test script
├── test_api.py                              # Level B4 12-endpoint integration test suite
└── zerowaste.db                             # Initialized SQLite database
```

### 5.2 Flutter Client Directory (`app_Mena/`)

```text
f:/Development/Projects/Mobile-Apps/app_Mena/
├── android/
│   └── app/src/main/AndroidManifest.xml     # Configured with INTERNET & Cleartext permissions
├── lib/
│   ├── core/
│   │   ├── config/
│   │   │   ├── app_config.dart              # Platform-aware baseUrl & useMock toggle
│   │   │   └── mock_database.dart           # Offline mock singleton for testing isolation
│   │   ├── network/
│   │   │   └── dio_client.dart              # Configured Dio HTTP client with JWT interceptor
│   │   ├── offline/
│   │   │   └── offline_queue_service.dart   # Hive offline approval/audit buffering & auto-sync
│   │   ├── router/
│   │   │   ├── app_router.dart              # GoRouter with auth redirection & 5 tab branches
│   │   │   └── scaffold_with_nav_bar.dart   # Persistent shell with store switcher dropdown
│   │   └── theme/
│   │       ├── app_colors.dart              # Brand palette (Forest Green, Mint, Status colors)
│   │       └── app_theme.dart               # Material 3 theme definitions
│   ├── features/
│   │   ├── alerts/
│   │   │   ├── data/
│   │   │   │   ├── datasources/
│   │   │   │   │   ├── alerts_mock_datasource.dart
│   │   │   │   │   └── alerts_remote_datasource.dart
│   │   │   │   ├── models/
│   │   │   │   │   └── alert_model.dart     # SpoilageAlert JSON serialization
│   │   │   │   └── repositories/
│   │   │   │       ├── mock_alerts_repository.dart
│   │   │   │       └── remote_alerts_repository.dart
│   │   │   ├── domain/
│   │   │   │   ├── models/
│   │   │   │   │   └── spoilage_alert.dart  # Pure Dart immutable SpoilageAlert entity
│   │   │   │   └── repositories/
│   │   │   │       └── alerts_repository.dart
│   │   │   └── presentation/
│   │   │       ├── alerts_providers.dart    # Riverpod repository & data providers
│   │   │       ├── screens/
│   │   │       │   └── alerts_screen.dart   # Responsive alerts list with summary headers
│   │   │       └── widgets/
│   │   │           └── alert_card.dart      # Urgency indicators & 25%/40% markdown action buttons
│   │   ├── analytics/
│   │   │   ├── data/
│   │   │   │   ├── datasources/
│   │   │   │   │   ├── analytics_mock_datasource.dart
│   │   │   │   │   └── analytics_remote_datasource.dart
│   │   │   │   ├── models/
│   │   │   │   │   └── analytics_models.dart # WasteMetrics, SalesPoint, CategoryWaste JSON models
│   │   │   │   └── repositories/
│   │   │   │       ├── mock_analytics_repository.dart
│   │   │   │       └── remote_analytics_repository.dart
│   │   │   ├── domain/
│   │   │   │   ├── models/
│   │   │   │   │   └── waste_metrics.dart   # Pure Dart entities for sustainability analytics
│   │   │   │   └── repositories/
│   │   │   │       └── analytics_repository.dart
│   │   │   └── presentation/
│   │   │       ├── analytics_providers.dart # Riverpod analytics future providers
│   │   │       └── screens/
│   │   │           └── analytics_screen.dart # 3 fl_chart cards (Actual vs Pred, Avoided, Category)
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   │   ├── datasources/
│   │   │   │   │   ├── auth_mock_datasource.dart
│   │   │   │   │   └── auth_remote_datasource.dart
│   │   │   │   ├── models/
│   │   │   │   │   └── user_model.dart      # UserModel & StoreModel JSON mapping
│   │   │   │   └── repositories/
│   │   │   │       ├── mock_auth_repository.dart
│   │   │   │       └── remote_auth_repository.dart
│   │   │   ├── domain/
│   │   │   │   ├── models/
│   │   │   │   │   └── app_user.dart        # Pure Dart AppUser & Store entities
│   │   │   │   └── repositories/
│   │   │   │       └── auth_repository.dart
│   │   │   └── presentation/
│   │   │       ├── auth_providers.dart      # currentUserProvider & activeStoreIdProvider
│   │   │       └── screens/
│   │   │           └── login_screen.dart    # Staff login with Quick Demo Login button
│   │   ├── catalog/
│   │   │   ├── data/
│   │   │   │   ├── datasources/
│   │   │   │   │   ├── catalog_mock_datasource.dart
│   │   │   │   │   └── catalog_remote_datasource.dart
│   │   │   │   ├── models/
│   │   │   │   │   └── catalog_models.dart  # ProductModel, BatchModel, AuditEntryModel
│   │   │   │   └── repositories/
│   │   │   │       ├── mock_catalog_repository.dart
│   │   │   │       └── remote_catalog_repository.dart
│   │   │   ├── domain/
│   │   │   │   ├── models/
│   │   │   │   │   └── product.dart         # Pure Dart Product, ProductBatch, AuditEntry entities
│   │   │   │   └── repositories/
│   │   │   │       └── catalog_repository.dart
│   │   │   └── presentation/
│   │   │       ├── catalog_providers.dart   # productsProvider & productBatchesProvider
│   │   │       ├── screens/
│   │   │       │   └── catalog_screen.dart  # Category chips, 300ms debounced search, urgency sort
│   │   │       └── widgets/
│   │   │           ├── closing_audit_dialog.dart # Full-screen on-hand/spoilage audit dialog
│   │   │           └── product_card.dart    # Product item with batch bottom sheet
│   │   ├── dashboard/
│   │   │   ├── data/
│   │   │   │   ├── datasources/
│   │   │   │   │   ├── dashboard_mock_datasource.dart
│   │   │   │   │   └── dashboard_remote_datasource.dart
│   │   │   │   └── repositories/
│   │   │   │       ├── mock_dashboard_repository.dart
│   │   │   │       └── remote_dashboard_repository.dart
│   │   │   ├── domain/
│   │   │   │   └── repositories/
│   │   │   │       └── dashboard_repository.dart
│   │   │   └── presentation/
│   │   │       ├── dashboard_providers.dart # dashboardMetricsProvider
│   │   │       └── screens/
│   │   │           └── dashboard_screen.dart # 4 adaptive KPI cards & eco impact tracker
│   │   └── reorder/
│   │       ├── data/
│   │       │   ├── datasources/
│   │       │   │   ├── reorder_mock_datasource.dart
│   │       │   │   └── reorder_remote_datasource.dart
│   │       │   ├── models/
│   │       │   │   └── reorder_models.dart  # RecommendationModel & ApprovalRequestModel
│   │       │   └── repositories/
│   │       │       ├── mock_reorder_repository.dart
│   │       │       └── remote_reorder_repository.dart
│   │       ├── domain/
│   │       │   ├── models/
│   │       │   │   └── recommendation.dart  # Recommendation & ApprovalRequest entities
│   │       │   └── repositories/
│   │       │       └── reorder_repository.dart
│   │       └── presentation/
│   │           ├── reorder_providers.dart   # recommendationsProvider & override state
│   │           ├── screens/
│   │           │   └── reorder_screen.dart  # Grouped recommendations & Approve All button
│   │           └── widgets/
│   │               └── recommendation_card.dart # Stepper override, reason code & XAI card
│   └── main.dart                            # Hive initialization & application entrypoint
├── test/
│   └── widget_test.dart                     # End-to-end integration widget test suite (6/6 passing)
├── pubspec.yaml                             # Package dependencies & assets
└── README.md                                # Comprehensive developer & deployment guide
```

---

## 6. End-to-End Implementation Roadmap & Completed Levels

### 6.1 Backend Track
* **B0 (API Contract):** Complete REST JSON contract defined and locked (`api_contract_v1.md`).
* **B1 (FastAPI & ML Inference):** Serialized LightGBM loaded into memory, input aligned with 192 features, demand prediction with non-negative constraints and TreeSHAP driver extraction verified via `test_ml.py`.
* **B2 (Database & 60-Day History Seeder):** 9 SQLAlchemy relational models created; seeded 3 stores, 45 products, 57 batches, 2,745 inventory snapshots (60+ days), and 183 weather/mobility telemetry records into `zerowaste.db`.
* **B3 (Feature Pipeline & Newsvendor Engine):** Exact 192-feature builder implemented, Newsvendor critical fractile optimization ($CF = \frac{Cu}{Cu+Co}$) programmed with `scipy.stats.norm.ppf`, and dynamic markdown alert logic verified via `test_b3.py`.
* **B4 (Full REST API Endpoints & Auth):** 12 REST API endpoints implemented with JWT token verification and CORS middleware. Complete integration verified via `test_api.py`.

### 6.2 Flutter Track
* **Level 0 (Foundation & Router):** Material 3 Eco-theme, `AppConfig`, GoRouter with 5 indexed-stack navigation branches, and clean architecture folder scaffold.
* **Level 1 (Domain Models & Mock State):** Pure immutable Dart entities, repository interfaces, and in-memory mock database.
* **Level 2 (Auth, Guards & Store Switcher):** Login screen with validation, route redirection guards, and persistent multi-store switcher in the AppBar.
* **Level 3 (Dashboard KPIs & Catalog Audit):** 4 real-time KPI cards, category filter chips, 300ms debounced search, expiry urgency sort, batch inspection sheet, and full closing inventory audit dialog.
* **Level 4 (Smart Reorder Core & TreeSHAP XAI):** Prioritized replenishment cards, instant single-tap approve, bulk "Approve All", numeric stepper override with mandatory reason code, and expandable "Why this amount?" XAI cards.
* **Level 5 (Spoilage Alerts & fl_chart Analytics):** Spoilage alerts with color-coded urgency ($0\text{d}, 1\text{d}, 2\text{d}$) and 25%/40% discount acceptance; 3 interactive `fl_chart` data visualizations.
* **Level 6 (Real API Integration & Hive Offline Queue):** Dio HTTP client with JWT interceptor, JSON data models in `data/models/`, remote data sources, and Hive offline buffering queue for order approvals and stock audits.
* **Level 7 (Polish, Responsiveness & Startup Auto-Sync):** Responsive tablet/desktop layouts (`maxWidth: 900`, 4-column KPI grid), startup auto-flush of offline changes (`syncOfflineQueue`), "Quick Demo Login" button, clean `flutter analyze` (0 issues), and full widget test pass (6/6).

---

## 7. Complete Screen-by-Screen Walkthrough

1. **Staff Portal (`LoginScreen`):**
   * Secure access control with input validation.
   * "Quick Demo Login" instantly populates credentials (`manager@zerowaste.com` / `password123`) for testing.
2. **Command Center (`DashboardScreen`):**
   * Real-time operational metrics: Units at Spoilage Risk, Dollar Exposure, Pending Replenishment Orders, and Cumulative Food/Carbon Saved.
   * Branch Switcher in the top AppBar dynamically recalibrates all screen data for Store 1, 2, or 3.
3. **Perishable Catalog (`CatalogScreen`):**
   * Filterable by category (*Produce*, *Dairy*, *Bakery*, *Butchery*).
   * 300ms debounced instant search and shelf-life urgency ordering.
   * Tapping any product opens a bottom sheet detailing individual delivery batches, expiration dates, and remaining quantities.
   * Floating Action Button opens the **Closing Inventory Audit** dialog to record physical stock and discarded spoilage.
4. **AI Replenishment (`ReorderScreen`):**
   * Displays prioritized replenishment recommendations generated by the LightGBM/Newsvendor pipeline.
   * Store managers can tap **Approve** on individual cards or use **Approve All**.
   * Tapping **Override** presents a numeric stepper and reason code selector.
   * Tapping **"Why this amount?"** opens the TreeSHAP insight card detailing the environmental and historical drivers behind the recommendation.
5. **Dynamic Spoilage Alerts (`AlertsScreen`):**
   * Flags inventory batches nearing expiration ($\le 2$ days) where remaining stock exceeds expected sales demand.
   * Recommends optimal salvage markdowns (e.g., *Apply 40% discount to clear remaining 15 units today*).
   * Managers can **Accept Markdown** (synchronizing discount to POS) or **Dismiss**.
6. **Performance Analytics (`AnalyticsScreen`):**
   * **Actual vs. Predicted Sales:** 30-day dual-line chart tracking machine learning forecasting precision.
   * **Cumulative Waste Reduction:** Upward-sloping trend showing historical units of food diverted from disposal.
   * **Waste by Category:** Bar chart showing discarded units across grocery departments.

---

## 8. Verification, Testing & Quality Assurance

### 8.1 Backend Verification Suite
* **`python test_ml.py`**: Initial model inference & TreeSHAP driver extraction passed ($100\%$).
* **`python test_b3.py`**: Mathematical 192-feature construction & Newsvendor engine passed ($100\%$).
* **`python test_api.py`**: All 12 REST API endpoints verified sequentially ($100\%$ passed).

### 8.2 Flutter Verification Suite
* **`flutter analyze`**:
  ```text
  Analyzing app_Mena...
  No issues found! (ran in 3.8s)
  ```
  *(Zero errors, zero warnings, zero linter diagnostics).*

* **`flutter test`**:
  ```text
  00:00 +0: loading test/widget_test.dart
  00:00 +0: Unauthenticated user is redirected to LoginScreen
  00:00 +1: Authenticated user lands on Dashboard and sees KPI cards
  00:00 +2: Navigate to Catalog and verify category chips and products
  00:01 +3: Navigate to Reorder tab and verify recommendation cards
  00:01 +4: Navigate to Alerts tab and verify alert cards and actions
  00:01 +5: Navigate to Analytics tab and verify three chart sections
  00:02 +6: All tests passed!
  ```

---

## 9. Step-by-Step Local Execution Guide

### Step 1: Start the Backend Server
```powershell
cd f:\Development\Projects\Mobile-Apps\backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
* **Swagger API Explorer:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

### Step 2: Run the Flutter Mobile App
```powershell
cd f:\Development\Projects\Mobile-Apps\app_Mena
flutter run
```
* On Android Emulator, the app automatically targets `http://10.0.2.2:8000/api/v1`.
* On Windows Desktop / Web, the app targets `http://127.0.0.1:8000/api/v1`.
* On Login Screen: Tap **"Quick Demo Login"** for instant 1-click access.
