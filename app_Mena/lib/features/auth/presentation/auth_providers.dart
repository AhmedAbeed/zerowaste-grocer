import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../data/repositories/remote_auth_repository.dart';
import '../domain/models/app_user.dart';
import '../domain/repositories/auth_repository.dart';

/// Currently authenticated user, or null if unauthenticated / logged out
final currentUserProvider = StateProvider<AppUser?>((ref) => null);

/// Currently selected active store ID (defaults to Store #1)
final activeStoreIdProvider = StateProvider<int>((ref) => 1);

/// Repository provider for Auth
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return RemoteAuthRepository(dio: dio);
});

/// Read call provider fetching available grocery stores
final storesProvider = FutureProvider<List<Store>>((ref) async {
  final repository = ref.watch(authRepositoryProvider);
  return repository.getStores();
});
