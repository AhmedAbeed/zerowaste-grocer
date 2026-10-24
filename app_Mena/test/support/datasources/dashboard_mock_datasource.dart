import '../mock_database.dart';
import 'package:zerowaste_grocer/features/analytics/domain/models/waste_metrics.dart';

class DashboardMockDataSource {
  final MockDatabase _db = MockDatabase.instance;

  Future<WasteMetrics> getSummary(int storeId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getMetrics(storeId);
  }
}
