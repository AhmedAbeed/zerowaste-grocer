import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../../../core/notifications/local_notification_service.dart';
import '../../alerts/presentation/alerts_providers.dart';
import '../../auth/domain/models/app_user.dart';
import '../../auth/presentation/auth_providers.dart';
import '../../dashboard/presentation/dashboard_providers.dart';
import '../data/datasources/notifications_remote_datasource.dart';
import '../data/repositories/remote_notifications_repository.dart';
import '../domain/models/app_notification.dart';
import '../domain/repositories/notifications_repository.dart';

/// Repository provider for Notifications
final notificationsRepositoryProvider = Provider<NotificationsRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return RemoteNotificationsRepository(NotificationsRemoteDataSource(dio));
});

/// Pure top-level function selecting notifications to show to the user.
/// Rules:
/// - ignore notifications whose id is in alreadyShown
/// - sort the rest oldest-first by createdAt
/// - individual = the first maxIndividual of them
/// - extraCount = remaining count (0 if none)
({List<AppNotification> individual, int extraCount}) selectNotificationsToShow(
  List<AppNotification> unread,
  Set<int> alreadyShown, {
  int maxIndividual = 3,
}) {
  final available = unread.where((n) => !alreadyShown.contains(n.id)).toList();
  available.sort((a, b) => a.createdAt.compareTo(b.createdAt));

  if (available.length <= maxIndividual) {
    return (individual: available, extraCount: 0);
  } else {
    final individual = available.sublist(0, maxIndividual);
    final extraCount = available.length - maxIndividual;
    return (individual: individual, extraCount: extraCount);
  }
}

/// In-memory session tracking for notification IDs already shown
final Set<int> _sessionShownNotificationIds = {};

/// State notifier managing notifications polling and local alert dispatching
class NotificationsNotifier extends StateNotifier<NotificationsResult> {
  NotificationsNotifier(
    this.ref, {
    this.user,
    this.storeId = 1,
    NotificationsResult? initial,
  }) : super(initial ?? const NotificationsResult(items: [], unreadCount: 0)) {
    if (initial == null && user?.role == UserRole.storeManager) {
      _startPolling();
    }
  }

  final Ref? ref;
  final AppUser? user;
  final int storeId;
  Timer? _timer;

  void _startPolling() {
    _timer?.cancel();
    poll();
    _timer = Timer.periodic(const Duration(seconds: 60), (_) => poll());
  }

  Future<void> poll() async {
    final currentRef = ref;
    if (currentRef == null) return;
    try {
      if (user?.role != UserRole.storeManager) {
        if (mounted) {
          state = const NotificationsResult(items: [], unreadCount: 0);
        }
        return;
      }

      final repo = currentRef.read(notificationsRepositoryProvider);
      final result = await repo.fetch(storeId: storeId, unreadOnly: true);
      if (!mounted) return;

      final previousIds = state.items.map((n) => n.id).toSet();
      final hasNewNotification = result.items.any((n) => !previousIds.contains(n.id));
      if (hasNewNotification) {
        currentRef.invalidate(alertsProvider);
        currentRef.invalidate(dashboardMetricsProvider);
      }

      state = result;

      final selection = selectNotificationsToShow(result.items, _sessionShownNotificationIds);
      final localService = currentRef.read(localNotificationServiceProvider);

      for (final item in selection.individual) {
        _sessionShownNotificationIds.add(item.id);
        await localService.show(
          id: item.id,
          title: item.title,
          body: item.body,
        );
      }

      if (selection.extraCount > 0) {
        await localService.show(
          id: 999999,
          title: 'ZeroWaste Grocer',
          body: '${selection.extraCount} more spoilage alerts',
        );
      }
    } catch (_) {
      // Swallowed silently so it never throws, never shows error UI, and never touches offline queue
    }
  }

  Future<void> markAllRead() async {
    final currentRef = ref;
    if (currentRef == null) return;
    try {
      final repo = currentRef.read(notificationsRepositoryProvider);
      final unreadItems = state.items.where((n) => !n.isRead).toList();
      if (mounted) {
        state = NotificationsResult(
          items: state.items.map((e) => e.copyWith(isRead: true)).toList(),
          unreadCount: 0,
        );
      }
      await Future.wait(
        unreadItems.map((item) => repo.markRead(item.id).catchError((_) {})),
      );
      await poll();
    } catch (_) {
      // Swallowed silently
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _timer = null;
    super.dispose();
  }
}

/// Provider managing notification state and 60-second polling for store managers
final notificationsStateProvider =
    StateNotifierProvider<NotificationsNotifier, NotificationsResult>((ref) {
  final user = ref.watch(currentUserProvider);
  final storeId = ref.watch(activeStoreIdProvider);
  return NotificationsNotifier(ref, user: user, storeId: storeId);
});

/// Helper function to mark all unread notifications read for the active store and refresh state
Future<void> markAllReadForStore(dynamic ref) async {
  try {
    final notifier = ref.read(notificationsStateProvider.notifier);
    await notifier.markAllRead();
  } catch (_) {
    // Swallowed silently
  }
}
