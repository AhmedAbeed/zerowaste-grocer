import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../../auth/presentation/auth_providers.dart';
import '../data/repositories/remote_reorder_repository.dart';
import '../domain/models/recommendation.dart';
import '../domain/repositories/reorder_repository.dart';

/// Repository provider for Reorder
final reorderRepositoryProvider = Provider<ReorderRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return RemoteReorderRepository(dio: dio);
});

/// Read call provider for replenishment recommendations in the active store
final recommendationsProvider = FutureProvider<List<Recommendation>>((ref) async {
  final storeId = ref.watch(activeStoreIdProvider);
  final repository = ref.watch(reorderRepositoryProvider);
  return repository.getRecommendations(storeId);
});

/// Local map of override reasons per product ID (productId -> reason string)
final recommendationOverrideReasonsProvider = StateProvider<Map<int, String>>((ref) => {});
