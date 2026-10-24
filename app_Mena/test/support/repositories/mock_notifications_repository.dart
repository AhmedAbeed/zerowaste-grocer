import 'package:zerowaste_grocer/features/notifications/domain/models/app_notification.dart';
import 'package:zerowaste_grocer/features/notifications/domain/repositories/notifications_repository.dart';
import '../datasources/notifications_mock_datasource.dart';

class MockNotificationsRepository implements NotificationsRepository {
  MockNotificationsRepository({NotificationsMockDataSource? dataSource})
      : _dataSource = dataSource ?? NotificationsMockDataSource();

  final NotificationsMockDataSource _dataSource;

  @override
  Future<NotificationsResult> fetch({required int storeId, bool unreadOnly = false}) =>
      _dataSource.fetch(storeId: storeId, unreadOnly: unreadOnly);

  @override
  Future<void> markRead(int id) => _dataSource.markRead(id);
}
