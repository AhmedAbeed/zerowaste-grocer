import 'package:dio/dio.dart';
import 'package:zerowaste_grocer/features/analytics/data/datasources/analytics_remote_datasource.dart';
import 'package:zerowaste_grocer/features/analytics/domain/models/waste_metrics.dart';

class DashboardRemoteDataSource {
  DashboardRemoteDataSource(Dio dio)
      : _analyticsRemoteDataSource = AnalyticsRemoteDataSource(dio);

  final AnalyticsRemoteDataSource _analyticsRemoteDataSource;

  Future<WasteMetrics> getSummary(int storeId) {
    return _analyticsRemoteDataSource.getMetrics(storeId);
  }
}
