import 'package:zerowaste_grocer/features/notifications/domain/models/app_notification.dart';

class NotificationsMockDataSource {
  Future<NotificationsResult> fetch({required int storeId, bool unreadOnly = false}) async {
    await Future.delayed(const Duration(milliseconds: 50));
    return const NotificationsResult(items: [], unreadCount: 0);
  }

  Future<void> markRead(int id) async {
    await Future.delayed(const Duration(milliseconds: 50));
  }
}
