import '../mock_database.dart';
import 'package:zerowaste_grocer/features/reorder/domain/models/recommendation.dart';

class ReorderMockDataSource {
  final MockDatabase _db = MockDatabase.instance;

  Future<List<Recommendation>> getRecommendations(int storeId, [DateTime? targetDate]) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getRecommendations(storeId, targetDate);
  }

  Future<bool> approve(ApprovalRequest request) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.approveRecommendations(request);
  }
}
