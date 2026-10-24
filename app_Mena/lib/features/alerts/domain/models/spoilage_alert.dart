/// Lifecycle status of a markdown / spoilage alert.
enum AlertStatus {
  open,
  accepted,
  dismissed,
}

/// Alert flagged for batches nearing expiration with surplus units over predicted demand.
class SpoilageAlert {
  const SpoilageAlert({
    required this.id,
    this.batchId,
    required this.productId,
    required this.productName,
    required this.daysToExpiry,
    required this.remainingQty,
    required this.predictedDemand,
    required this.suggestedDiscountPct,
    required this.status,
    this.appliedDiscountPct,
  });

  final String id;
  final String? batchId;
  final int productId;
  final String productName;
  final int daysToExpiry;
  final int remainingQty;
  final int predictedDemand;
  final double suggestedDiscountPct;
  final AlertStatus status;
  final double? appliedDiscountPct;


  SpoilageAlert copyWith({
    String? id,
    String? batchId,
    int? productId,
    String? productName,
    int? daysToExpiry,
    int? remainingQty,
    int? predictedDemand,
    double? suggestedDiscountPct,
    AlertStatus? status,
    double? appliedDiscountPct,
  }) {
    return SpoilageAlert(
      id: id ?? this.id,
      batchId: batchId ?? this.batchId,
      productId: productId ?? this.productId,
      productName: productName ?? this.productName,
      daysToExpiry: daysToExpiry ?? this.daysToExpiry,
      remainingQty: remainingQty ?? this.remainingQty,
      predictedDemand: predictedDemand ?? this.predictedDemand,
      suggestedDiscountPct: suggestedDiscountPct ?? this.suggestedDiscountPct,
      status: status ?? this.status,
      appliedDiscountPct: appliedDiscountPct ?? this.appliedDiscountPct,
    );
  }
}
