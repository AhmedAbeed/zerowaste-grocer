import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../../auth/presentation/auth_providers.dart';
import '../data/repositories/remote_analytics_repository.dart';
import '../domain/models/waste_metrics.dart';
import '../domain/repositories/analytics_repository.dart';

/// Repository provider for Analytics
final analyticsRepositoryProvider = Provider<AnalyticsRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return RemoteAnalyticsRepository(dio: dio);
});

/// Read call provider for overall waste metrics in the active store
final analyticsMetricsProvider = FutureProvider<WasteMetrics>((ref) async {
  final storeId = ref.watch(activeStoreIdProvider);
  final repository = ref.watch(analyticsRepositoryProvider);
  return repository.getMetrics(storeId);
});

/// Read call provider for 30-day actual vs predicted sales series
final analyticsSalesSeriesProvider = FutureProvider<List<SalesPoint>>((ref) async {
  final storeId = ref.watch(activeStoreIdProvider);
  final repository = ref.watch(analyticsRepositoryProvider);
  return repository.getSalesSeries(storeId);
});

/// Read call provider for waste breakdown across categories
final analyticsCategoryWasteProvider = FutureProvider<List<CategoryWaste>>((ref) async {
  final storeId = ref.watch(activeStoreIdProvider);
  final repository = ref.watch(analyticsRepositoryProvider);
  return repository.getCategoryWaste(storeId);
});

// Aliases for backwards compatibility
final salesSeriesProvider = analyticsSalesSeriesProvider;
final categoryWasteProvider = analyticsCategoryWasteProvider;
