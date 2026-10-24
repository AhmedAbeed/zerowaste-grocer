import 'package:dio/dio.dart';
import '../../domain/models/app_notification.dart';
import '../models/notification_model.dart';

class NotificationsRemoteDataSource {
  const NotificationsRemoteDataSource(this._dio);

  final Dio _dio;

  Future<NotificationsResult> fetch({required int storeId, bool unreadOnly = false}) async {
    final response = await _dio.get(
      '/notifications',
      queryParameters: {
        'store_id': storeId,
        'unread_only': unreadOnly,
      },
    );

    final data = response.data as Map<String, dynamic>;
    return NotificationsListModel.fromJson(data).toDomain();
  }

  Future<void> markRead(int id) async {
    await _dio.post('/notifications/$id/read');
  }
}
