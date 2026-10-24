import '../models/waste_metrics.dart';

abstract class AnalyticsRepository {
  Future<WasteMetrics> getMetrics(int storeId);
  Future<List<SalesPoint>> getSalesSeries(int storeId);
  Future<List<CategoryWaste>> getCategoryWaste(int storeId);
}
