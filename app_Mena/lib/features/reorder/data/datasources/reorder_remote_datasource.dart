import 'package:dio/dio.dart';
import 'package:intl/intl.dart';
import '../../domain/models/recommendation.dart';
import '../models/reorder_models.dart';

class ReorderRemoteDataSource {
  const ReorderRemoteDataSource(this._dio);

  final Dio _dio;

  Future<List<Recommendation>> getRecommendations(int storeId, [DateTime? targetDate]) async {
    final queryParams = <String, dynamic>{
      'store_id': storeId,
    };
    if (targetDate != null) {
      queryParams['target_date'] = DateFormat('yyyy-MM-dd').format(targetDate);
    }
    final response = await _dio.get(
      '/replenishment/recommendations',
      queryParameters: queryParams,
    );

    final data = response.data as Map<String, dynamic>;
    final items = data['items'] as List<dynamic>? ?? [];
    return items
        .map((item) => RecommendationModel.fromJson(item as Map<String, dynamic>).toDomain())
        .toList();
  }

  Future<bool> approve(ApprovalRequest request) async {
    final response = await _dio.post(
      '/replenishment/approve',
      data: ApprovalRequestModel.toJson(request),
    );
    return response.statusCode == 200 || response.statusCode == 201;
  }
}
