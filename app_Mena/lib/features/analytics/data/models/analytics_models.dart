import 'package:zerowaste_grocer/features/catalog/domain/models/product.dart';
import '../../domain/models/waste_metrics.dart';

class WasteMetricsModel {
  const WasteMetricsModel({
    required this.unitsAtRisk,
    required this.projectedExposure,
    required this.pendingOrders,
    required this.kgSaved,
    required this.co2Saved,
  });

  factory WasteMetricsModel.fromJson(Map<String, dynamic> json) {
    return WasteMetricsModel(
      unitsAtRisk: (json['units_at_risk'] as num?)?.toInt() ?? 0,
      projectedExposure: (json['projected_exposure'] as num?)?.toDouble() ?? 0.0,
      pendingOrders: (json['pending_orders'] as num?)?.toInt() ?? 0,
      kgSaved: (json['kg_saved'] as num?)?.toDouble() ?? 0.0,
      co2Saved: (json['co2_saved'] as num?)?.toDouble() ?? 0.0,
    );
  }

  final int unitsAtRisk;
  final double projectedExposure;
  final int pendingOrders;
  final double kgSaved;
  final double co2Saved;

  WasteMetrics toDomain() {
    return WasteMetrics(
      unitsAtRisk: unitsAtRisk,
      projectedExposure: projectedExposure,
      pendingOrders: pendingOrders,
      kgSaved: kgSaved,
      co2Saved: co2Saved,
    );
  }
}

class SalesPointModel {
  const SalesPointModel({
    required this.date,
    required this.actual,
    required this.predicted,
  });

  factory SalesPointModel.fromJson(Map<String, dynamic> json) {
    return SalesPointModel(
      date: DateTime.parse(json['date'] as String),
      actual: (json['actual'] as num?)?.toDouble() ?? 0.0,
      predicted: (json['predicted'] as num?)?.toDouble() ?? 0.0,
    );
  }

  final DateTime date;
  final double actual;
  final double predicted;

  SalesPoint toDomain() {
    return SalesPoint(
      date: date,
      actual: actual,
      predicted: predicted,
    );
  }
}

class CategoryWasteModel {
  const CategoryWasteModel({
    required this.category,
    required this.units,
  });

  factory CategoryWasteModel.fromJson(Map<String, dynamic> json) {
    final catStr = (json['category'] as String? ?? 'produce').toLowerCase();
    ProductCategory category;
    switch (catStr) {
      case 'dairy':
        category = ProductCategory.dairy;
        break;
      case 'bakery':
        category = ProductCategory.bakery;
        break;
      case 'butchery':
        category = ProductCategory.butchery;
        break;
      case 'produce':
      default:
        category = ProductCategory.produce;
        break;
    }

    return CategoryWasteModel(
      category: category,
      units: (json['units'] as num?)?.toInt() ?? 0,
    );
  }

  final ProductCategory category;
  final int units;

  CategoryWaste toDomain() {
    return CategoryWaste(
      category: category,
      units: units,
    );
  }
}
