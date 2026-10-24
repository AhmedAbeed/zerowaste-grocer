import 'package:zerowaste_grocer/features/analytics/domain/models/waste_metrics.dart';

abstract class DashboardRepository {
  Future<WasteMetrics> getSummary(int storeId);
}
