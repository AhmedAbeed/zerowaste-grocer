import '../../domain/models/app_notification.dart';
import '../../domain/repositories/notifications_repository.dart';
import '../datasources/notifications_remote_datasource.dart';

class RemoteNotificationsRepository implements NotificationsRepository {
  const RemoteNotificationsRepository(this._dataSource);

  final NotificationsRemoteDataSource _dataSource;

  @override
  Future<NotificationsResult> fetch({required int storeId, bool unreadOnly = false}) =>
      _dataSource.fetch(storeId: storeId, unreadOnly: unreadOnly);

  @override
  Future<void> markRead(int id) => _dataSource.markRead(id);
}
