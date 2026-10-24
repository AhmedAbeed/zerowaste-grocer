import 'package:zerowaste_grocer/features/alerts/domain/models/spoilage_alert.dart';
import 'package:zerowaste_grocer/features/alerts/domain/repositories/alerts_repository.dart';
import '../datasources/alerts_mock_datasource.dart';

class MockAlertsRepository implements AlertsRepository {
  MockAlertsRepository({AlertsMockDataSource? dataSource})
      : _dataSource = dataSource ?? AlertsMockDataSource();

  final AlertsMockDataSource _dataSource;

  @override
  Future<List<SpoilageAlert>> getAlerts(int storeId) => _dataSource.getAlerts(storeId);

  @override
  Future<void> acceptMarkdown(String alertId) => _dataSource.acceptMarkdown(alertId);

  @override
  Future<void> dismiss(String alertId) => _dataSource.dismiss(alertId);
}
