import 'package:zerowaste_grocer/features/catalog/domain/models/product.dart';

/// Aggregated waste and sustainability performance metrics.
class WasteMetrics {
  const WasteMetrics({
    required this.unitsAtRisk,
    required this.projectedExposure,
    required this.pendingOrders,
    required this.kgSaved,
    required this.co2Saved,
  });

  final int unitsAtRisk;
  final double projectedExposure;
  final int pendingOrders;
  final double kgSaved;
  final double co2Saved;

  WasteMetrics copyWith({
    int? unitsAtRisk,
    double? projectedExposure,
    int? pendingOrders,
    double? kgSaved,
    double? co2Saved,
  }) {
    return WasteMetrics(
      unitsAtRisk: unitsAtRisk ?? this.unitsAtRisk,
      projectedExposure: projectedExposure ?? this.projectedExposure,
      pendingOrders: pendingOrders ?? this.pendingOrders,
      kgSaved: kgSaved ?? this.kgSaved,
      co2Saved: co2Saved ?? this.co2Saved,
    );
  }
}

/// A single day's data point comparing actual revenue to backend ML predictions.
class SalesPoint {
  const SalesPoint({
    required this.date,
    required this.actual,
    required this.predicted,
  });

  final DateTime date;
  final double actual;
  final double predicted;
}

/// Waste tracking aggregated by product category.
class CategoryWaste {
  const CategoryWaste({
    required this.category,
    required this.units,
  });

  final ProductCategory category;
  final int units;
}
