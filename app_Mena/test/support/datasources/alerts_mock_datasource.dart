import '../mock_database.dart';
import 'package:zerowaste_grocer/features/alerts/domain/models/spoilage_alert.dart';

class AlertsMockDataSource {
  final MockDatabase _db = MockDatabase.instance;

  Future<List<SpoilageAlert>> getAlerts(int storeId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getAlerts(storeId);
  }

  Future<void> acceptMarkdown(String alertId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    _db.acceptMarkdown(alertId);
  }

  Future<void> dismiss(String alertId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    _db.dismissAlert(alertId);
  }
}
