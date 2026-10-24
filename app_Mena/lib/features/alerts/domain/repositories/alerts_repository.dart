import '../models/spoilage_alert.dart';

abstract class AlertsRepository {
  Future<List<SpoilageAlert>> getAlerts(int storeId);
  Future<void> acceptMarkdown(String alertId);
  Future<void> dismiss(String alertId);
}
