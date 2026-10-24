import 'package:dio/dio.dart';
import '../../domain/models/spoilage_alert.dart';
import '../../domain/repositories/alerts_repository.dart';
import '../datasources/alerts_remote_datasource.dart';

class RemoteAlertsRepository implements AlertsRepository {
  RemoteAlertsRepository({AlertsRemoteDataSource? remoteDataSource, Dio? dio})
      : _remoteDataSource = remoteDataSource ?? AlertsRemoteDataSource(dio ?? Dio());

  final AlertsRemoteDataSource _remoteDataSource;

  @override
  Future<List<SpoilageAlert>> getAlerts(int storeId) {
    return _remoteDataSource.getAlerts(storeId);
  }

  @override
  Future<void> acceptMarkdown(String alertId) {
    return _remoteDataSource.acceptMarkdown(alertId);
  }

  @override
  Future<void> dismiss(String alertId) {
    return _remoteDataSource.dismiss(alertId);
  }
}
