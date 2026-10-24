import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../../auth/presentation/auth_providers.dart';
import '../data/repositories/remote_alerts_repository.dart';
import '../domain/models/spoilage_alert.dart';
import '../domain/repositories/alerts_repository.dart';

/// Repository provider for Alerts
final alertsRepositoryProvider = Provider<AlertsRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return RemoteAlertsRepository(dio: dio);
});

/// Read call provider for markdown and spoilage alerts in the active store
final alertsProvider = FutureProvider<List<SpoilageAlert>>((ref) async {
  final storeId = ref.watch(activeStoreIdProvider);
  final repository = ref.watch(alertsRepositoryProvider);
  return repository.getAlerts(storeId);
});
