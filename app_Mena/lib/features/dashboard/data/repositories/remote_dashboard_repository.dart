import 'package:dio/dio.dart';
import 'package:zerowaste_grocer/features/analytics/domain/models/waste_metrics.dart';
import '../../domain/repositories/dashboard_repository.dart';
import '../datasources/dashboard_remote_datasource.dart';

class RemoteDashboardRepository implements DashboardRepository {
  RemoteDashboardRepository({DashboardRemoteDataSource? remoteDataSource, Dio? dio})
      : _remoteDataSource = remoteDataSource ?? DashboardRemoteDataSource(dio ?? Dio());

  final DashboardRemoteDataSource _remoteDataSource;

  @override
  Future<WasteMetrics> getSummary(int storeId) {
    return _remoteDataSource.getSummary(storeId);
  }
}
