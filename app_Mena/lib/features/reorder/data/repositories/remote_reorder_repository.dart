import 'package:dio/dio.dart';
import '../../../../core/offline/offline_queue_service.dart';
import '../../domain/models/recommendation.dart';
import '../../domain/repositories/reorder_repository.dart';
import '../datasources/reorder_remote_datasource.dart';

class RemoteReorderRepository implements ReorderRepository {
  RemoteReorderRepository({ReorderRemoteDataSource? remoteDataSource, Dio? dio})
      : _remoteDataSource = remoteDataSource ?? ReorderRemoteDataSource(dio ?? Dio());

  final ReorderRemoteDataSource _remoteDataSource;

  @override
  Future<List<Recommendation>> getRecommendations(int storeId, [DateTime? targetDate]) {
    return _remoteDataSource.getRecommendations(storeId, targetDate);
  }

  @override
  Future<bool> approve(ApprovalRequest request) async {
    try {
      return await _remoteDataSource.approve(request);
    } on DioException {
      // Optimistic offline approval buffered in Hive
      await OfflineQueueService.enqueueApproval(request);
      return true;
    } catch (_) {
      await OfflineQueueService.enqueueApproval(request);
      return true;
    }
  }
}
