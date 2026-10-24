import 'package:dio/dio.dart';
import '../../domain/models/spoilage_alert.dart';
import '../models/alert_model.dart';

class AlertsRemoteDataSource {
  const AlertsRemoteDataSource(this._dio);

  final Dio _dio;

  Future<List<SpoilageAlert>> getAlerts(int storeId) async {
    final response = await _dio.get(
      '/alerts',
      queryParameters: {'store_id': storeId},
    );

    final data = response.data as Map<String, dynamic>;
    final items = data['items'] as List<dynamic>? ?? [];
    return items
        .map((item) => AlertModel.fromJson(item as Map<String, dynamic>).toDomain())
        .toList();
  }

  Future<void> acceptMarkdown(String alertId) async {
    await _dio.post(
      '/inventory/markdown',
      data: {
        'alert_id': alertId,
        'action': 'accept',
      },
    );
  }

  Future<void> dismiss(String alertId) async {
    await _dio.post('/alerts/$alertId/dismiss');
  }
}
