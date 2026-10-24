import 'package:dio/dio.dart';
import '../../domain/models/waste_metrics.dart';
import '../../domain/repositories/analytics_repository.dart';
import '../datasources/analytics_remote_datasource.dart';

class RemoteAnalyticsRepository implements AnalyticsRepository {
  RemoteAnalyticsRepository({AnalyticsRemoteDataSource? remoteDataSource, Dio? dio})
      : _remoteDataSource = remoteDataSource ?? AnalyticsRemoteDataSource(dio ?? Dio());

  final AnalyticsRemoteDataSource _remoteDataSource;

  @override
  Future<WasteMetrics> getMetrics(int storeId) {
    return _remoteDataSource.getMetrics(storeId);
  }

  @override
  Future<List<SalesPoint>> getSalesSeries(int storeId) {
    return _remoteDataSource.getSalesSeries(storeId);
  }

  @override
  Future<List<CategoryWaste>> getCategoryWaste(int storeId) {
    return _remoteDataSource.getCategoryWaste(storeId);
  }
}
