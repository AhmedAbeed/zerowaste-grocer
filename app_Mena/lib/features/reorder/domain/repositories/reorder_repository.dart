import '../models/recommendation.dart';

abstract class ReorderRepository {
  Future<List<Recommendation>> getRecommendations(int storeId, [DateTime? targetDate]);
  Future<bool> approve(ApprovalRequest request);
}
