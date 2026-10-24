import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../../analytics/domain/models/waste_metrics.dart';
import '../../auth/presentation/auth_providers.dart';
import '../data/repositories/remote_dashboard_repository.dart';
import '../domain/repositories/dashboard_repository.dart';

/// Repository provider for Dashboard
final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return RemoteDashboardRepository(dio: dio);
});

/// Read call provider for high-level dashboard summary metrics in the active store
final dashboardMetricsProvider = FutureProvider<WasteMetrics>((ref) async {
  final storeId = ref.watch(activeStoreIdProvider);
  final repository = ref.watch(dashboardRepositoryProvider);
  return repository.getSummary(storeId);
});

/// Alias for backwards compatibility
final dashboardSummaryProvider = dashboardMetricsProvider;
