# ZeroWaste Grocer

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Client-Flutter_3.24+-02569B.svg?logo=flutter&logoColor=white)](https://flutter.dev)
[![LightGBM](https://img.shields.io/badge/ML-LightGBM_Quantile-FFA000.svg)](https://lightgbm.readthedocs.io/)
[![WCAG 2.1 AA](https://img.shields.io/badge/Accessibility-WCAG_2.1_AA_Compliant-success.svg)](https://www.w3.org/WAI/WCAG21/quickref/)
[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC_BY--NC--ND_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

**ZeroWaste Grocer** is an enterprise AI-powered grocery inventory management and waste prevention platform. It combines machine learning demand forecasting (LightGBM quantile regression), dynamic expiration markdown execution, explainable AI (XAI) replenishment recommendations, and closing inventory stock audits to minimize retail food waste while maximizing store operational margins.

---

## Key Features

- **Automated Spoilage Alerts & Dynamic Markdown**:
  - Batches expiring within $\le 3$ days are automatically surfaced with urgency tags.
  - Recommended markdowns (10% to 50%) calculated dynamically to clear surplus before spoilage.
  - One-click markdown application instantly updates database pricing.
- **Explainable AI Replenishment (XAI)**:
  - 7-day quantile demand forecasting built with 192 features (lag sales, rolling statistics, calendar seasonality, price elasticity).
  - Expandable *"Why this amount?"* panels displaying natural language rationale and top feature impact drivers.
  - Full support for supervisor manual overrides with mandatory reason recording.
- **Role-Based Access Control (RBAC)**:
  - Three distinct enterprise roles: **Store Manager**, **Inventory Auditor**, and **System Administrator**.
  - Strict symmetric authorization on Flutter client navigation and FastAPI backend endpoints.
- **Real-Time Sustainability & Waste KPIs**:
  - Live tracking of Projected Waste Exposure, Units at Risk, Waste Trend Charts, CO₂e Saved, and Kilograms Rescued.
- **Accessible Dual Theme (Light & Dark Mode)**:
  - WCAG 2.1 AA compliant contrast ratios across all text elements ($\ge 14.8:1$) and chart series ($\ge 5.3:1$).
  - One-click theme toggle persisted locally via Hive key-value storage (`settings_box`).
- **Offline & Low-Bandwidth Resilience**:
  - Hive offline action queuing with automatic synchronization when connectivity is restored.

---

## Seeded User Accounts

The system comes pre-seeded with deterministic realistic accounts:

| Role | Email | Password | Assigned Store | Core Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Store Manager** | `manager@zerowaste.com` | `password123` | Store #1 (Metro Downtown) | Full store oversight: Dashboard, Catalog, Reorder (Approve/Override), Alerts (Accept/Dismiss), Analytics |
| **Inventory Auditor** | `auditor@zerowaste.com` | `auditor123` | Store #1 | Restricted access: Catalog inspection and Closing Inventory Stock Audit dialog only |
| **System Admin** | `admin@zerowaste.com` | `admin123` | All Stores (1, 2, 3) | Multi-store oversight: Store switcher dropdown, Enterprise Dashboard, Global Catalog, Alerts read-only oversight |

---

## Technology Stack

- **Frontend Client**: Flutter (Web, iOS, Android), Riverpod 2.5 State Management, GoRouter, FlChart, Hive Flutter.
- **Backend API**: FastAPI, Python 3.10+, SQLAlchemy, Pydantic v2, Uvicorn, PassLib (Bcrypt), PyJWT.
- **Machine Learning**: LightGBM (Quantile Loss), Scikit-Learn, Pandas, NumPy.
- **Storage**: SQLite with deterministic golden baseline restore scripts.
- **Quality & E2E**: Playwright (Headless Chromium, Video Recording, Trace Viewer), Flutter Test Suite.

---

## Getting Started

### 1. Prerequisites
- Python 3.10 or higher (Python 3.14 compatible)
- Flutter SDK 3.24 or higher
- Google Chrome (for Flutter Web and Playwright testing)

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Reset database to verified golden baseline
python reset_db.py

# Launch FastAPI development server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
API documentation is accessible at `http://127.0.0.1:8000/docs`.

### 3. Flutter Web Client Setup
```bash
# Navigate to client directory
cd app_Mena

# Install dependencies
flutter pub get

# Run on Chrome
flutter run -d chrome --web-port 5000

# Or build for production release
flutter build web --release
```

---

## Quality Assurance & Verification

ZeroWaste Grocer includes an automated test and contract verification suite:

```bash
# Run comprehensive multi-suite check (Backend + Flutter)
cd backend
python run_all_checks.py --flutter

# Run Flutter static analysis
cd ../app_Mena
flutter analyze

# Run Flutter unit & contrast tests
flutter test

# Run Playwright E2E Dark Mode Verification
python F:\Temp\qa_dark\verify_dark_playwright.py
```

---

## Documentation

For full architectural flowcharts, sequence diagrams, and screen-by-screen references, see:
- [Detailed User Flow Specification](docs/USER_FLOW.md)
- [Architectural Diagrams](docs/diagrams/)
- [Screen Capture Gallery](docs/screens/)

---

## Dataset & Licensing

- **License**: The software application code is distributed under the terms of the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)** license.
- **Dataset Notice**: Under the provisions of CC BY-NC-ND 4.0, raw underlying supermarket sales datasets are proprietary and excluded from this repository. Serialized ML model weights are distributed within `backend/app/ml/models/` for out-of-the-box local inference.
