import '../mock_database.dart';
import 'package:zerowaste_grocer/features/analytics/domain/models/waste_metrics.dart';

class AnalyticsMockDataSource {
  final MockDatabase _db = MockDatabase.instance;

  Future<WasteMetrics> getMetrics(int storeId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getMetrics(storeId);
  }

  Future<List<SalesPoint>> getSalesSeries(int storeId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getSalesSeries(storeId);
  }

  Future<List<CategoryWaste>> getCategoryWaste(int storeId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getCategoryWaste(storeId);
  }
}
