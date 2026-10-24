import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/intl.dart';

import 'package:zerowaste_grocer/features/alerts/data/datasources/alerts_remote_datasource.dart';
import 'package:zerowaste_grocer/features/analytics/data/datasources/analytics_remote_datasource.dart';
import 'package:zerowaste_grocer/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:zerowaste_grocer/features/auth/domain/models/app_user.dart';
import 'package:zerowaste_grocer/features/catalog/data/datasources/catalog_remote_datasource.dart';
import 'package:zerowaste_grocer/features/catalog/domain/models/product.dart';
import 'package:zerowaste_grocer/features/notifications/data/datasources/notifications_remote_datasource.dart';
import 'package:zerowaste_grocer/features/reorder/data/datasources/reorder_remote_datasource.dart';

void main() {
  final liveUrl = Platform.environment['ZEROWASTE_LIVE_URL'];
  final skipReason = (liveUrl == null || liveUrl.isEmpty)
      ? 'Set ZEROWASTE_LIVE_URL (e.g. http://127.0.0.1:8000) to run'
      : null;

  group('Live Backend Contract Tests', skip: skipReason, () {
    late Dio dio;
    late AuthRemoteDataSource authDataSource;
    late CatalogRemoteDataSource catalogDataSource;
    late ReorderRemoteDataSource reorderDataSource;
    late AlertsRemoteDataSource alertsDataSource;
    late NotificationsRemoteDataSource notificationsDataSource;
    late AnalyticsRemoteDataSource analyticsDataSource;

    AppUser? managerUser;
    List<Product> store1Products = [];

    setUpAll(() {
      if (liveUrl == null || liveUrl.isEmpty) return;

      final baseUrl = liveUrl.endsWith('/api/v1')
          ? liveUrl
          : (liveUrl.endsWith('/') ? '${liveUrl}api/v1' : '$liveUrl/api/v1');

      dio = Dio(
        BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 15),
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        ),
      );

      authDataSource = AuthRemoteDataSource(dio);
      catalogDataSource = CatalogRemoteDataSource(dio);
      reorderDataSource = ReorderRemoteDataSource(dio);
      alertsDataSource = AlertsRemoteDataSource(dio);
      notificationsDataSource = NotificationsRemoteDataSource(dio);
      analyticsDataSource = AnalyticsRemoteDataSource(dio);
    });

    test('L1 login: parses into the user model; role == storeManager; store_id == 1', () async {
      managerUser = await authDataSource.login('manager@zerowaste.com', 'password123');

      expect(managerUser, isNotNull);
      expect(managerUser!.role, UserRole.storeManager);
      expect(managerUser!.storeId, 1);
      expect(managerUser!.token, isNotEmpty);

      // Attach token to subsequent Dio requests
      dio.options.headers['Authorization'] = 'Bearer ${managerUser!.token}';

      // ignore: avoid_print
      print('[L1 PASSED] Login parsed: User ${managerUser!.name}, role=${managerUser!.role.name}, store_id=${managerUser!.storeId}');
    });

    test('L2 stores list: exactly 3 stores parse', () async {
      final stores = await authDataSource.getStores();

      expect(stores.length, 3);
      for (final s in stores) {
        expect(s.id, greaterThan(0));
        expect(s.name, isNotEmpty);
        expect(s.location, isNotEmpty);
      }

      // ignore: avoid_print
      print('[L2 PASSED] Stores list: ${stores.length} stores parsed (First: Store #${stores.first.id} - ${stores.first.name})');
    });

    test('L3 store 1 inventory/products: 15 products parse; each has non-empty name and a category', () async {
      store1Products = await catalogDataSource.getProducts(1);

      expect(store1Products.length, 15);
      for (final p in store1Products) {
        expect(p.name, isNotEmpty);
        expect(p.category, isNotNull);
        expect(p.unitCost, greaterThan(0));
        expect(p.unitPrice, greaterThan(0));
      }

      // ignore: avoid_print
      print('[L3 PASSED] Store 1 inventory: ${store1Products.length} products parsed (First: ${store1Products.first.name}, category=${store1Products.first.category.name})');
    });

    test('L4 batches of the first product: parse without error (print count)', () async {
      expect(store1Products, isNotEmpty);
      final firstProductId = store1Products.first.id;
      final batches = await catalogDataSource.getBatches(firstProductId);

      expect(batches, isA<List<ProductBatch>>());
      final sampleBatch = batches.isNotEmpty ? batches.first.id : 'none';

      // ignore: avoid_print
      print('[L4 PASSED] Batches of product #$firstProductId (${store1Products.first.name}): ${batches.length} batches parsed (Sample Batch: $sampleBatch)');
    });

    test('L5 recommendations for store 1 for today AND for tomorrow (yyyy-MM-dd): 15 items parse each time', () async {
      final now = DateTime.now();
      final tomorrow = now.add(const Duration(days: 1));
      final dateTodayStr = DateFormat('yyyy-MM-dd').format(now);

      // Raw JSON inspection of first recommendation item
      final rawTodayRes = await dio.get(
        '/replenishment/recommendations',
        queryParameters: {'store_id': 1, 'target_date': dateTodayStr},
      );
      final rawTodayData = rawTodayRes.data as Map<String, dynamic>;
      final rawItems = rawTodayData['items'] as List<dynamic>;
      expect(rawItems, isNotEmpty);
      final firstRawItem = rawItems.first as Map<String, dynamic>;

      // ignore: avoid_print
      print('Raw first recommendation JSON: ${jsonEncode(firstRawItem)}');

      // Assert sigma fields directly on raw JSON without fallback
      expect(firstRawItem.containsKey('sigma_source'), isTrue);
      expect(firstRawItem.containsKey('sigma_e'), isTrue);
      final sigmaSource = firstRawItem['sigma_source'];
      final sigmaE = firstRawItem['sigma_e'];
      expect(sigmaSource, isIn(['rolling', 'fallback']));
      expect(sigmaE, isA<num>());
      expect((sigmaE as num).toDouble(), greaterThanOrEqualTo(1.0));

      // Domain model parsing checks
      final recsToday = await reorderDataSource.getRecommendations(1, now);
      final recsTomorrow = await reorderDataSource.getRecommendations(1, tomorrow);

      expect(recsToday.length, 15);
      expect(recsTomorrow.length, 15);

      for (final r in [...recsToday, ...recsTomorrow]) {
        expect(r.recommendedQty, greaterThanOrEqualTo(0));
        expect(r.xaiDrivers.length, 3);
        final sum = r.xaiDrivers.fold<double>(0.0, (acc, d) => acc + d.impactPct);
        expect((sum - 100.0).abs(), lessThanOrEqualTo(0.1));
      }

      // ignore: avoid_print
      print('[L5 PASSED] Recommendations: 15 today (first: ${recsToday.first.productName}, qty=${recsToday.first.recommendedQty}, sigma_e=$sigmaE, sigma_source=$sigmaSource) & 15 tomorrow (first: ${recsTomorrow.first.productName}, qty=${recsTomorrow.first.recommendedQty}) parsed with 3 XAI drivers');
    });

    test('L6 alerts for store 1: parse without error; every alert batch id is a String', () async {
      final alerts = await alertsDataSource.getAlerts(1);

      expect(alerts, isNotEmpty);
      for (final a in alerts) {
        expect(a.batchId, isNotNull);
        expect(a.batchId, isA<String>());
        expect(a.batchId, isNotEmpty);
        expect(a.daysToExpiry, lessThanOrEqualTo(2));
      }

      // ignore: avoid_print
      print('[L6 PASSED] Alerts for store 1: ${alerts.length} alerts parsed (First: ${alerts.first.productName}, batchId=${alerts.first.batchId}, discount=${(alerts.first.suggestedDiscountPct * 100).toInt()}%)');
    });

    test('L7 POST /alerts/run-now, then notifications for store 1: parse without error; at least 1 item', () async {
      final runNowRes = await dio.post('/alerts/run-now');
      expect(runNowRes.statusCode, 200);

      final notifsRes = await notificationsDataSource.fetch(storeId: 1);

      expect(notifsRes.items.length, greaterThanOrEqualTo(1));
      expect(notifsRes.unreadCount, greaterThanOrEqualTo(notifsRes.items.length));

      for (final n in notifsRes.items) {
        expect(n.batchId, isNotNull);
        expect(n.batchId, isA<String>());
        expect(n.batchId, isNotEmpty);
        expect(n.createdAt, isA<DateTime>());
        expect(n.isRead, isFalse);
      }

      // ignore: avoid_print
      print('[L7 PASSED] POST /alerts/run-now & Notifications: ${notifsRes.items.length} notifications parsed (unreadCount=${notifsRes.unreadCount}, first batchId=${notifsRes.items.first.batchId})');
    });

    test('L8 mark ONE notification as read through the real remote datasource; verify unreadCount decreased by 1', () async {
      final notifsBefore = await notificationsDataSource.fetch(storeId: 1);
      expect(notifsBefore.items, isNotEmpty);

      final targetNotif = notifsBefore.items.first;
      final initialUnread = notifsBefore.unreadCount;

      await notificationsDataSource.markRead(targetNotif.id);

      final notifsAfter = await notificationsDataSource.fetch(storeId: 1);
      expect(notifsAfter.unreadCount, initialUnread - 1);

      // ignore: avoid_print
      print('[L8 PASSED] Mark notification #${targetNotif.id} read: unreadCount decreased from $initialUnread to ${notifsAfter.unreadCount}');
    });

    test('L9 analytics: waste-metrics, sales-series, category-waste for store 1: all three parse without error', () async {
      final metrics = await analyticsDataSource.getMetrics(1);
      final series = await analyticsDataSource.getSalesSeries(1);
      final catWaste = await analyticsDataSource.getCategoryWaste(1);

      expect(metrics.unitsAtRisk, greaterThanOrEqualTo(0));
      expect(metrics.projectedExposure, greaterThanOrEqualTo(0.0));
      expect(series, isNotEmpty);
      expect(catWaste, isNotEmpty);

      // ignore: avoid_print
      print('[L9 PASSED] Analytics: metrics (risk=${metrics.unitsAtRisk}, exposure=\$${metrics.projectedExposure.toStringAsFixed(1)}), series=${series.length} points, categoryWaste=${catWaste.length} categories parsed');
    });

    test('L10 dismiss alert via remote datasource with batchId, verify alert count decreased by 1 and batch is absent', () async {
      final alertsBefore = await alertsDataSource.getAlerts(1);
      expect(alertsBefore, isNotEmpty);

      final targetAlert = alertsBefore.first;
      final targetBatchId = targetAlert.batchId!;
      final initialCount = alertsBefore.length;

      // Dismiss using the value the app now sends: alert.batchId
      await alertsDataSource.dismiss(targetBatchId);

      final alertsAfter = await alertsDataSource.getAlerts(1);
      expect(alertsAfter.length, initialCount - 1);
      expect(alertsAfter.any((a) => a.batchId == targetBatchId), isFalse);

      // Informational print (no assert) calling with full alert ID
      try {
        final infoRes = await dio.post('/alerts/ALT-1-B-SPN-201/dismiss');
        // ignore: avoid_print
        print('INFORMATIONAL: POST /alerts/ALT-1-B-SPN-201/dismiss status: ${infoRes.statusCode}');
      } on DioException catch (e) {
        // ignore: avoid_print
        print('INFORMATIONAL: POST /alerts/ALT-1-B-SPN-201/dismiss returned status: ${e.response?.statusCode} (detail: ${e.response?.data})');
      }

      // ignore: avoid_print
      print('[L10 PASSED] Dismissed alert for batch $targetBatchId: count decreased from $initialCount to ${alertsAfter.length}, batch confirmed absent');
    });
  });
}
