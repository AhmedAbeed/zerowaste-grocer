import '../models/app_notification.dart';

abstract class NotificationsRepository {
  Future<NotificationsResult> fetch({required int storeId, bool unreadOnly = false});
  Future<void> markRead(int id);
}
