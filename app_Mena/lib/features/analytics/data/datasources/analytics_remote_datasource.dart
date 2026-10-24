import 'package:dio/dio.dart';
import '../../domain/models/waste_metrics.dart';
import '../models/analytics_models.dart';

class AnalyticsRemoteDataSource {
  const AnalyticsRemoteDataSource(this._dio);

  final Dio _dio;

  Future<WasteMetrics> getMetrics(int storeId) async {
    final response = await _dio.get(
      '/analytics/waste-metrics',
      queryParameters: {'store_id': storeId},
    );

    final data = response.data as Map<String, dynamic>;
    return WasteMetricsModel.fromJson(data).toDomain();
  }

  Future<List<SalesPoint>> getSalesSeries(int storeId) async {
    final response = await _dio.get(
      '/analytics/sales-series',
      queryParameters: {'store_id': storeId},
    );

    final list = response.data as List<dynamic>;
    return list
        .map((item) => SalesPointModel.fromJson(item as Map<String, dynamic>).toDomain())
        .toList();
  }

  Future<List<CategoryWaste>> getCategoryWaste(int storeId) async {
    final response = await _dio.get(
      '/analytics/category-waste',
      queryParameters: {'store_id': storeId},
    );

    final list = response.data as List<dynamic>;
    return list
        .map((item) => CategoryWasteModel.fromJson(item as Map<String, dynamic>).toDomain())
        .toList();
  }
}
