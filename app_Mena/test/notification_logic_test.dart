import 'package:flutter_test/flutter_test.dart';
import 'support/repositories/mock_alerts_repository.dart';
import 'package:zerowaste_grocer/features/notifications/domain/models/app_notification.dart';
import 'package:zerowaste_grocer/features/notifications/presentation/notifications_providers.dart';

void main() {
  group('selectNotificationsToShow', () {
    final now = DateTime(2026, 10, 22, 10, 0, 0);

    test('5 unread, none shown -> individual has the 3 OLDEST, extraCount 2', () {
      final unread = [
        AppNotification(
          id: 5,
          storeId: 1,
          type: 'SPOILAGE_MARKDOWN',
          title: 'Alert 5',
          body: 'Body 5',
          createdAt: now.add(const Duration(minutes: 50)),
          isRead: false,
        ),
        AppNotification(
          id: 1,
          storeId: 1,
          type: 'SPOILAGE_MARKDOWN',
          title: 'Alert 1',
          body: 'Body 1',
          createdAt: now.add(const Duration(minutes: 10)),
          isRead: false,
        ),
        AppNotification(
          id: 4,
          storeId: 1,
          type: 'SPOILAGE_MARKDOWN',
          title: 'Alert 4',
          body: 'Body 4',
          createdAt: now.add(const Duration(minutes: 40)),
          isRead: false,
        ),
        AppNotification(
          id: 2,
          storeId: 1,
          type: 'SPOILAGE_MARKDOWN',
          title: 'Alert 2',
          body: 'Body 2',
          createdAt: now.add(const Duration(minutes: 20)),
          isRead: false,
        ),
        AppNotification(
          id: 3,
          storeId: 1,
          type: 'SPOILAGE_MARKDOWN',
          title: 'Alert 3',
          body: 'Body 3',
          createdAt: now.add(const Duration(minutes: 30)),
          isRead: false,
        ),
      ];

      final result = selectNotificationsToShow(unread, {});

      expect(result.individual.length, 3);
      expect(result.extraCount, 2);
      expect(result.individual.map((n) => n.id).toList(), [1, 2, 3]);
    });

    test('ids already in alreadyShown are excluded', () {
      final unread = [
        AppNotification(
          id: 1,
          storeId: 1,
          type: 'SPOILAGE_MARKDOWN',
          title: 'Alert 1',
          body: 'Body 1',
          createdAt: now.add(const Duration(minutes: 10)),
          isRead: false,
        ),
        AppNotification(
          id: 2,
          storeId: 1,
          type: 'SPOILAGE_MARKDOWN',
          title: 'Alert 2',
          body: 'Body 2',
          createdAt: now.add(const Duration(minutes: 20)),
          isRead: false,
        ),
        AppNotification(
          id: 3,
          storeId: 1,
          type: 'SPOILAGE_MARKDOWN',
          title: 'Alert 3',
          body: 'Body 3',
          createdAt: now.add(const Duration(minutes: 30)),
          isRead: false,
        ),
      ];

      final result = selectNotificationsToShow(unread, {1, 2});

      expect(result.individual.length, 1);
      expect(result.extraCount, 0);
      expect(result.individual.first.id, 3);
    });

    test('empty input -> empty individual, extraCount 0', () {
      final result = selectNotificationsToShow([], {});

      expect(result.individual, isEmpty);
      expect(result.extraCount, 0);
    });

    test('MockAlertsRepository dismiss removes alert from in-memory list', () async {
      final repo = MockAlertsRepository();
      final alerts = await repo.getAlerts(1);
      expect(alerts.isNotEmpty, isTrue);
      final firstId = alerts.first.id;
      await repo.dismiss(firstId);
      final updated = await repo.getAlerts(1);
      expect(updated.any((a) => a.id == firstId), isFalse);
    });
  });
}
