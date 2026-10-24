import 'package:zerowaste_grocer/features/analytics/domain/models/waste_metrics.dart';
import 'package:zerowaste_grocer/features/analytics/domain/repositories/analytics_repository.dart';
import '../datasources/analytics_mock_datasource.dart';

class MockAnalyticsRepository implements AnalyticsRepository {
  MockAnalyticsRepository({AnalyticsMockDataSource? dataSource})
      : _dataSource = dataSource ?? AnalyticsMockDataSource();

  final AnalyticsMockDataSource _dataSource;

  @override
  Future<WasteMetrics> getMetrics(int storeId) => _dataSource.getMetrics(storeId);

  @override
  Future<List<SalesPoint>> getSalesSeries(int storeId) => _dataSource.getSalesSeries(storeId);

  @override
  Future<List<CategoryWaste>> getCategoryWaste(int storeId) => _dataSource.getCategoryWaste(storeId);
}
