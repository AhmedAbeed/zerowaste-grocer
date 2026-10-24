import 'package:zerowaste_grocer/features/reorder/domain/models/recommendation.dart';
import 'package:zerowaste_grocer/features/reorder/domain/repositories/reorder_repository.dart';
import '../datasources/reorder_mock_datasource.dart';

class MockReorderRepository implements ReorderRepository {
  MockReorderRepository({ReorderMockDataSource? dataSource})
      : _dataSource = dataSource ?? ReorderMockDataSource();

  final ReorderMockDataSource _dataSource;

  @override
  Future<List<Recommendation>> getRecommendations(int storeId, [DateTime? targetDate]) =>
      _dataSource.getRecommendations(storeId, targetDate);

  @override
  Future<bool> approve(ApprovalRequest request) => _dataSource.approve(request);
}
