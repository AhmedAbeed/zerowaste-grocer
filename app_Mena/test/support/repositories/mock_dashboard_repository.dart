import 'package:zerowaste_grocer/features/analytics/domain/models/waste_metrics.dart';
import 'package:zerowaste_grocer/features/dashboard/domain/repositories/dashboard_repository.dart';
import '../datasources/dashboard_mock_datasource.dart';

class MockDashboardRepository implements DashboardRepository {
  MockDashboardRepository({DashboardMockDataSource? dataSource})
      : _dataSource = dataSource ?? DashboardMockDataSource();

  final DashboardMockDataSource _dataSource;

  @override
  Future<WasteMetrics> getSummary(int storeId) => _dataSource.getSummary(storeId);
}
