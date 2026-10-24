import '../../domain/models/spoilage_alert.dart';

class AlertModel {
  const AlertModel({
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

  factory AlertModel.fromJson(Map<String, dynamic> json) {
    final statusStr = (json['status'] as String? ?? 'open').toLowerCase();
    AlertStatus status;
    switch (statusStr) {
      case 'accepted':
        status = AlertStatus.accepted;
        break;
      case 'dismissed':
        status = AlertStatus.dismissed;
        break;
      case 'open':
      default:
        status = AlertStatus.open;
        break;
    }

    final rawId = json['id'] as String? ?? '';
    final batchId = json['batch_id'] as String? ??
        (rawId.startsWith('ALT-') ? rawId.split('-').sublist(2).join('-') : (rawId.isNotEmpty ? rawId : null));

    return AlertModel(
      id: rawId,
      batchId: batchId,
      productId: (json['product_id'] as num).toInt(),
      productName: json['product_name'] as String? ?? '',
      daysToExpiry: (json['days_to_expiry'] as num).toInt(),
      remainingQty: (json['remaining_qty'] as num).toInt(),
      predictedDemand: (json['predicted_demand'] as num).toInt(),
      suggestedDiscountPct: (json['suggested_discount_pct'] as num?)?.toDouble() ?? 0.25,
      status: status,
      appliedDiscountPct: (json['applied_discount_pct'] as num?)?.toDouble(),
    );
  }

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


  SpoilageAlert toDomain() {
    return SpoilageAlert(
      id: id,
      batchId: batchId,
      productId: productId,
      productName: productName,
      daysToExpiry: daysToExpiry,
      remainingQty: remainingQty,
      predictedDemand: predictedDemand,
      suggestedDiscountPct: suggestedDiscountPct,
      status: status,
      appliedDiscountPct: appliedDiscountPct,
    );
  }
}
