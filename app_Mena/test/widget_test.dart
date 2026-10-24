import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'support/mock_database.dart';
import 'support/mock_provider_overrides.dart';
import 'package:zerowaste_grocer/features/alerts/presentation/widgets/alert_card.dart';
import 'package:zerowaste_grocer/features/auth/domain/models/app_user.dart';
import 'package:zerowaste_grocer/features/auth/presentation/auth_providers.dart';
import 'package:zerowaste_grocer/features/catalog/presentation/widgets/product_card.dart';
import 'package:zerowaste_grocer/features/notifications/domain/models/app_notification.dart';
import 'package:zerowaste_grocer/features/notifications/presentation/notifications_providers.dart';
import 'package:zerowaste_grocer/features/reorder/presentation/widgets/recommendation_card.dart';
import 'package:zerowaste_grocer/main.dart';
import 'package:zerowaste_grocer/core/theme/app_colors.dart';
import 'package:zerowaste_grocer/features/catalog/domain/models/product.dart';
import 'package:zerowaste_grocer/features/catalog/presentation/catalog_providers.dart';

void main() {
  testWidgets('Unauthenticated user is redirected to LoginScreen', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Staff Portal'), findsOneWidget);
    expect(find.widgetWithText(ElevatedButton, 'Log In'), findsOneWidget);
  });

  testWidgets('Authenticated user lands on Dashboard and sees KPI cards', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Mena Mikhail',
              role: UserRole.storeManager,
              token: 'test_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Store Dashboard'), findsOneWidget);
    expect(find.text('Units at Risk'), findsOneWidget);
    expect(find.text('Projected Exposure'), findsOneWidget);
    expect(find.text('Pending Orders'), findsOneWidget);
    expect(find.text('Kg Saved / CO₂e'), findsOneWidget);
  });

  testWidgets('Navigate to Catalog and verify category chips and products', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Mena Mikhail',
              role: UserRole.storeManager,
              token: 'test_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Catalog'));
    await tester.pumpAndSettle();

    expect(find.text('All'), findsOneWidget);
    expect(find.text('Produce'), findsOneWidget);
    expect(find.byType(ProductCard), findsWidgets);
    expect(find.text('Audit'), findsOneWidget);
  });

  testWidgets('Navigate to Reorder tab and verify recommendation cards', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Mena Mikhail',
              role: UserRole.storeManager,
              token: 'test_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Reorder'));
    await tester.pumpAndSettle();

    expect(find.text('AI Replenishment'), findsOneWidget);
    expect(find.byType(RecommendationCard), findsWidgets);
    expect(find.text('Why this amount?'), findsWidgets);
  });

  testWidgets('Navigate to Alerts tab and verify alert cards and actions', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Mena Mikhail',
              role: UserRole.storeManager,
              token: 'test_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Alerts'));
    await tester.pumpAndSettle();

    expect(find.byType(AlertCard), findsWidgets);
    expect(find.textContaining('active alerts'), findsOneWidget);
    expect(find.text('Accept Markdown'), findsWidgets);
    expect(find.text('Dismiss'), findsWidgets);
  });

  testWidgets('Navigate to Analytics tab and verify three chart sections', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Mena Mikhail',
              role: UserRole.storeManager,
              token: 'test_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Analytics'));
    await tester.pumpAndSettle();

    expect(find.text('Performance Analytics'), findsOneWidget);
    expect(find.text('Actual vs Predicted Sales'), findsOneWidget);
    expect(find.text('Cumulative Waste Reduction'), findsOneWidget);
    expect(find.text('Waste by Category'), findsOneWidget);
  });

  testWidgets('Inventory Auditor sees only the Catalog tab with audit action', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-002',
              name: 'Auditor User',
              role: UserRole.inventoryAuditor,
              token: 'auditor_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    // Verify role pill is present in AppBar
    expect(find.text('Auditor'), findsOneWidget);

    // Auditor sees only Catalog tab
    expect(find.text('Catalog'), findsOneWidget);
    expect(find.text('Dashboard'), findsNothing);
    expect(find.text('Reorder'), findsNothing);
    expect(find.text('Alerts'), findsNothing);
    expect(find.text('Analytics'), findsNothing);

    // Auditor sees the audit action on Catalog
    expect(find.text('Audit'), findsWidgets);
  });

  testWidgets('System Admin does not see the Reorder tab or the Approve button', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-003',
              name: 'Admin User',
              role: UserRole.systemAdmin,
              token: 'admin_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    // Verify role pill is present in AppBar
    expect(find.text('Admin'), findsOneWidget);

    // Admin sees Dashboard, Catalog, Alerts, Analytics
    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Catalog'), findsOneWidget);
    expect(find.text('Alerts'), findsOneWidget);
    expect(find.text('Analytics'), findsOneWidget);

    // Admin does NOT see Reorder tab
    expect(find.text('Reorder'), findsNothing);

    // Admin does NOT see Approve button
    expect(find.widgetWithText(ElevatedButton, 'Approve'), findsNothing);
    expect(find.textContaining('Approve All'), findsNothing);
  });

  testWidgets('Store Manager sees everything (all 5 tabs and Approve actions)', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Manager User',
              role: UserRole.storeManager,
              token: 'manager_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    // Verify role pill is present in AppBar
    expect(find.text('Manager'), findsOneWidget);

    // Manager sees all 5 navigation tabs
    expect(find.text('Dashboard'), findsOneWidget);
    expect(find.text('Catalog'), findsOneWidget);
    expect(find.text('Reorder'), findsOneWidget);
    expect(find.text('Alerts'), findsOneWidget);
    expect(find.text('Analytics'), findsOneWidget);

    // Navigate to Reorder tab and verify Approve actions are present
    await tester.tap(find.text('Reorder'));
    await tester.pumpAndSettle();

    expect(find.byType(RecommendationCard), findsWidgets);
    expect(find.widgetWithText(ElevatedButton, 'Approve'), findsWidgets);
  });

  testWidgets('Store Manager sees a badge with "3" on the Alerts tab', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Manager User',
              role: UserRole.storeManager,
              token: 'manager_token',
            ),
          ),
          notificationsStateProvider.overrideWith(
            (ref) => NotificationsNotifier(
              ref,
              user: const AppUser(
                id: 'USR-001',
                name: 'Manager User',
                role: UserRole.storeManager,
                token: 'manager_token',
              ),
              initial: NotificationsResult(items: [], unreadCount: 3),
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.widgetWithText(Badge, '3'), findsWidgets);
  });

  testWidgets('System Admin does NOT see the badge on Alerts tab', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-003',
              name: 'Admin User',
              role: UserRole.systemAdmin,
              token: 'admin_token',
            ),
          ),
          notificationsStateProvider.overrideWith(
            (ref) => NotificationsNotifier(
              ref,
              initial: NotificationsResult(items: [], unreadCount: 3),
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.widgetWithText(Badge, '3'), findsNothing);
  });

  testWidgets('In mock mode, tapping "Dismiss" on an alert card removes that card and shows SnackBar', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Manager User',
              role: UserRole.storeManager,
              token: 'manager_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Alerts'));
    await tester.pumpAndSettle();

    final initialAlertCards = find.byType(AlertCard);
    final initialCount = initialAlertCards.evaluate().length;
    expect(initialCount, greaterThan(0));
    final firstCard = tester.widget<AlertCard>(initialAlertCards.first);
    final firstDismissedId = firstCard.alert.id;

    await tester.tap(find.text('Dismiss').first);
    await tester.pumpAndSettle();

    expect(find.text('Alert postponed for 6 hours'), findsOneWidget);
    expect(find.byType(AlertCard), findsNWidgets(initialCount - 1));
    expect(find.byWidgetPredicate((w) => w is AlertCard && w.alert.id == firstDismissedId), findsNothing);
  });

  testWidgets("Store Manager sees both 'Dismiss' and 'Accept Markdown' on open alerts", (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Manager User',
              role: UserRole.storeManager,
              token: 'manager_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Alerts'));
    await tester.pumpAndSettle();

    expect(find.byType(AlertCard), findsWidgets);
    expect(find.text('Dismiss'), findsWidgets);
    expect(find.text('Accept Markdown'), findsWidgets);
  });

  testWidgets("System Admin sees NEITHER 'Dismiss' NOR 'Accept Markdown' on alert cards", (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-003',
              name: 'Admin User',
              role: UserRole.systemAdmin,
              token: 'admin_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Alerts'));
    await tester.pumpAndSettle();

    expect(find.byType(AlertCard), findsWidgets);
    expect(find.text('Dismiss'), findsNothing);
    expect(find.text('Accept Markdown'), findsNothing);
  });

  testWidgets("Batch urgency tag: days_to_expiry 1 -> 'Expires in 1d' (red) and 5 -> 'Expires in 5d' (green)", (WidgetTester tester) async {
    const testProduct = Product(
      id: 999,
      sku: 'TEST-SKU-1',
      name: 'Test Product',
      category: ProductCategory.produce,
      unitCost: 1.0,
      unitPrice: 2.0,
      shelfLifeDays: 7,
      safetyStock: 10,
      currentStock: 25,
    );

    final batches = [
      ProductBatch(
        id: 'B1',
        productId: 999,
        receivedDate: DateTime(2023, 6, 20),
        expirationDate: DateTime(2023, 7, 1),
        remainingQty: 10,
        discountPct: 0.0,
        daysToExpiry: 1,
      ),
      ProductBatch(
        id: 'B2',
        productId: 999,
        receivedDate: DateTime(2023, 6, 20),
        expirationDate: DateTime(2023, 7, 5),
        remainingQty: 15,
        discountPct: 0.0,
        daysToExpiry: 5,
      ),
    ];

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          productBatchesProvider(999).overrideWith((ref) => Future.value(batches)),
        ],
        child: const MaterialApp(
          home: Scaffold(
            body: ProductCard(product: testProduct),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // Tap ProductCard to open bottom sheet
    await tester.tap(find.byType(ProductCard));
    await tester.pumpAndSettle();

    final text1 = find.text('Expires in 1d');
    expect(text1, findsOneWidget);
    final textWidget1 = tester.widget<Text>(text1);
    expect(textWidget1.style?.color, equals(AppColors.critical));

    final text2 = find.text('Expires in 5d');
    expect(text2, findsOneWidget);
    final textWidget2 = tester.widget<Text>(text2);
    expect(textWidget2.style?.color, equals(AppColors.safe));
  });

  testWidgets("Batch urgency tag: fallback to DateTime.now() when daysToExpiry is null (mock mode)", (WidgetTester tester) async {
    const testProduct = Product(
      id: 998,
      sku: 'TEST-SKU-2',
      name: 'Mock Product',
      category: ProductCategory.produce,
      unitCost: 1.0,
      unitPrice: 2.0,
      shelfLifeDays: 7,
      safetyStock: 10,
      currentStock: 20,
    );

    final batches = [
      ProductBatch(
        id: 'M1',
        productId: 998,
        receivedDate: DateTime.now().subtract(const Duration(days: 2)),
        expirationDate: DateTime.now().add(const Duration(days: 5, hours: 2)),
        remainingQty: 10,
        discountPct: 0.0,
        daysToExpiry: null,
      ),
    ];

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          productBatchesProvider(998).overrideWith((ref) => Future.value(batches)),
        ],
        child: const MaterialApp(
          home: Scaffold(
            body: ProductCard(product: testProduct),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byType(ProductCard));
    await tester.pumpAndSettle();

    expect(find.text('Expires in 5d'), findsOneWidget);
  });

  testWidgets('Tap Accept Markdown in mock mode shows Markdown Applied and hides action buttons for that card', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith(
            (ref) => const AppUser(
              id: 'USR-001',
              name: 'Manager User',
              role: UserRole.storeManager,
              token: 'manager_token',
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Alerts'));
    await tester.pumpAndSettle();

    final initialAcceptCount = find.text('Accept Markdown').evaluate().length;
    expect(initialAcceptCount, greaterThan(0));

    // Tap Accept Markdown on the first card
    await tester.tap(find.text('Accept Markdown').first);
    await tester.pumpAndSettle();

    // Verify Markdown Applied is displayed on the card
    expect(find.textContaining('Markdown Applied'), findsWidgets);
    expect(find.textContaining('Markdown applied for'), findsOneWidget);

    // Verify Accept Markdown buttons decreased by 1
    expect(find.text('Accept Markdown'), findsNWidgets(initialAcceptCount - 1));

    // Find the accepted card and verify it has NO Accept Markdown or Dismiss buttons
    final acceptedCardFinder = find.ancestor(
      of: find.textContaining('Markdown Applied').first,
      matching: find.byType(AlertCard),
    );
    expect(acceptedCardFinder, findsOneWidget);
    expect(find.descendant(of: acceptedCardFinder, matching: find.text('Accept Markdown')), findsNothing);
    expect(find.descendant(of: acceptedCardFinder, matching: find.text('Dismiss')), findsNothing);
  });

  testWidgets('Alerts badge stays while another tab is active and disappears after selecting Alerts', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    const manager = AppUser(
      id: 'USR-001',
      name: 'Manager User',
      role: UserRole.storeManager,
      token: 'manager_token',
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith((ref) => manager),
          notificationsStateProvider.overrideWith(
            (ref) => NotificationsNotifier(
              ref,
              user: manager,
              initial: NotificationsResult(
                items: [
                  AppNotification(
                    id: 101,
                    storeId: 1,
                    type: 'spoilage_alert',
                    batchId: 'B-001',
                    title: 'Alert 1',
                    body: 'Test alert 1',
                    createdAt: DateTime(2026, 10, 24),
                    isRead: false,
                  ),
                ],
                unreadCount: 1,
              ),
            ),
          ),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    // While Dashboard is active, badge is visible on the Alerts tab
    expect(find.widgetWithText(Badge, '1'), findsWidgets);

    // Switch to Catalog tab (another tab is active)
    await tester.tap(find.text('Catalog'));
    await tester.pumpAndSettle();

    // Badge still stays visible while Catalog is active
    expect(find.widgetWithText(Badge, '1'), findsWidgets);

    // Now tap the Alerts tab to select it
    await tester.tap(find.text('Alerts'));
    await tester.pumpAndSettle();

    // Badge disappears after selecting Alerts tab (unread count marked read / 0)
    expect(find.widgetWithText(Badge, '1'), findsNothing);
  });

  testWidgets('Approve one card: persists Approved checkmark, decreases Approve All count, persists across tab switch', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1200, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
      MockDatabase.instance.resetRecommendations();
    });

    const manager = AppUser(
      id: 'USR-001',
      name: 'Manager User',
      role: UserRole.storeManager,
      token: 'manager_token',
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...mockRepositoryOverrides,
          currentUserProvider.overrideWith((ref) => manager),
        ],
        child: const ZeroWasteGrocerApp(),
      ),
    );
    await tester.pumpAndSettle();

    // Navigate to Reorder tab
    await tester.tap(find.text('Reorder'));
    await tester.pumpAndSettle();

    // Baseline: Approve All (10) is present
    expect(find.text('Approve All (10)'), findsOneWidget);

    // Tap the first Approve button (Organic Hass Avocados)
    final approveButtons = find.widgetWithText(ElevatedButton, 'Approve');
    expect(approveButtons, findsWidgets);
    await tester.tap(approveButtons.first);
    await tester.pumpAndSettle();

    // Verify Avocados card now displays Approved checkmark
    expect(find.text('Approved ✓'), findsWidgets);

    // Verify Approve All count decreased by 1 (to 9)
    expect(find.text('Approve All (9)'), findsOneWidget);

    // Switch to Dashboard tab
    await tester.tap(find.text('Dashboard'));
    await tester.pumpAndSettle();

    // Switch back to Reorder tab
    await tester.tap(find.text('Reorder'));
    await tester.pumpAndSettle();

    // Verify card STILL displays Approved checkmark after returning
    expect(find.text('Approved ✓'), findsWidgets);
    expect(find.text('Approve All (9)'), findsOneWidget);
  });
}
