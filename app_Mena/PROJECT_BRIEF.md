# PROJECT_BRIEF: ZeroWaste Grocer (Flutter app)

## What it is
Mobile app for grocery store managers. Shows AI-recommended order quantities for perishable products, expiry/markdown alerts, waste tracking and analytics. The ML model lives on the BACKEND only. The app just calls REST APIs and shows results. Never implement ML or the 192 features inside Flutter.

## Tech rules (mandatory)
- Flutter 3.x, Android + iOS
- Feature-first Clean Architecture: presentation / domain / data per feature
- State: Riverpod (AsyncNotifier)
- HTTP: Dio. Base URL read from one config file (easy to change)
- Local cache/offline queue: Hive
- Charts: fl_chart
- Routing: go_router
- Every repository is an interface with TWO implementations: Mock (fake data) and Remote (real API). One flag switches between them.

## Design
- Colors: Forest Green #1B5E20, Mint #2E7D32, Background #F7FBF7, Text #212121
- Status: Critical #D32F2F, Warning #F57C00, Safe #388E3C
- Clean, minimal, eco look. Support phone and tablet.

## Screens
1. Login + store switcher (Store 1/2/3). JWT. Roles: Store Manager, Inventory Auditor, System Admin
2. Dashboard: units at spoilage risk, projected spoilage $, orders pending approval, sustainability counter (kg saved, CO2e)
3. Product catalog: categories (Produce, Dairy, Bakery, Butchery), search (debounced), sort by expiry urgency, closing audit form (on-hand stock + discarded units)
4. Smart Reorder (core): list of recommended quantities, per-item stepper override (asks reason), "Approve All", "Why this amount?" card showing xai_reason
5. Markdown/Spoilage alerts: batches expiring within 2 days with surplus, button "Apply X% discount"
6. Analytics: Actual vs Predicted sales, cumulative waste reduction, waste by category

## API (base: /api/v1)
| Method | Path | Used by |
|---|---|---|
| POST | /auth/login | Login |
| GET | /stores/{store_id}/inventory | Catalog |
| POST | /inventory/audit | Audit form |
| GET | /replenishment/recommendations?store_id=&target_date=YYYY-MM-DD | Smart Reorder. Response: `{ "items": [...] }` |
| POST | /replenishment/approve | Approve. Success = HTTP 201 |
| POST | /inventory/markdown | Markdown alerts |
| GET | /analytics/waste-metrics | Analytics |

Known item fields (from DB): product_id, predicted_demand, recommended_qty, final_approved_qty, xai_reason.
UNKNOWN: exact JSON of every other endpoint. Build DTOs behind mapper functions so field names can be changed in ONE place.

## Offline
If approve fails (no network): save in Hive queue as pending, retry later with backoff.

## Order status values
PENDING, APPROVED, DISPATCHED, COMPLETED, CANCELLED

## Timeline
- Oct 26 - Nov 1: project setup, navigation, main screens
- Nov 2 - 4: more screens, sample data, basic product management
- Nov 17 - 23: inventory, expiry tracking, waste recording, replenishment
- Nov 24 - 30: analytics, polish
- Dec 1 - 6: testing, demo data
- Dec 7 - 13: final

## Do NOT
- Do not build a backend or load .joblib in the app
- Do not hardcode the base URL or secrets in widgets
- Do not invent API fields; use mocks clearly marked TODO until real JSON is confirmed
