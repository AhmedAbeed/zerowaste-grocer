import 'package:zerowaste_grocer/features/catalog/domain/models/product.dart';
import '../../domain/models/recommendation.dart';

class RecommendationModel {
  const RecommendationModel({
    required this.productId,
    required this.productName,
    required this.category,
    required this.currentStock,
    required this.safetyStock,
    required this.predictedDemand,
    required this.recommendedQty,
    required this.approvedQty,
    required this.status,
    required this.xaiReason,
    required this.xaiDrivers,
  });

  factory RecommendationModel.fromJson(Map<String, dynamic> json) {
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

    final isApproved = json['approved'] == true;
    final statusStr = (json['status'] as String? ?? 'pending').toLowerCase();
    RecommendationStatus status;
    if (isApproved || statusStr == 'approved') {
      status = RecommendationStatus.approved;
    } else if (statusStr == 'overridden') {
      status = RecommendationStatus.overridden;
    } else {
      status = RecommendationStatus.pending;
    }

    final rawDrivers = json['xai_drivers'] as List<dynamic>? ?? [];
    final drivers = rawDrivers.map((d) {
      final map = d as Map<String, dynamic>;
      return XaiDriver(
        label: map['label'] as String? ?? '',
        impactPct: (map['impact_pct'] as num?)?.toDouble() ?? 0.0,
      );
    }).toList();

    return RecommendationModel(
      productId: (json['product_id'] as num).toInt(),
      productName: json['product_name'] as String? ?? '',
      category: category,
      currentStock: (json['current_stock'] as num?)?.toInt() ?? 0,
      safetyStock: (json['safety_stock'] as num?)?.toInt() ?? 5,
      predictedDemand: (json['predicted_demand'] as num?)?.toInt() ?? 0,
      recommendedQty: (json['recommended_qty'] as num?)?.toInt() ?? 0,
      approvedQty: (json['approved_qty'] as num?)?.toInt() ?? (json['recommended_qty'] as num?)?.toInt() ?? 0,
      status: status,
      xaiReason: json['xai_reason'] as String? ?? '',
      xaiDrivers: drivers,
    );
  }

  final int productId;
  final String productName;
  final ProductCategory category;
  final int currentStock;
  final int safetyStock;
  final int predictedDemand;
  final int recommendedQty;
  final int approvedQty;
  final RecommendationStatus status;
  final String xaiReason;
  final List<XaiDriver> xaiDrivers;

  Recommendation toDomain() {
    return Recommendation(
      productId: productId,
      productName: productName,
      category: category,
      currentStock: currentStock,
      safetyStock: safetyStock,
      predictedDemand: predictedDemand,
      recommendedQty: recommendedQty,
      approvedQty: approvedQty,
      status: status,
      xaiReason: xaiReason,
      xaiDrivers: xaiDrivers,
    );
  }
}

class ApprovalRequestModel {
  static Map<String, dynamic> toJson(ApprovalRequest request) {
    return {
      'store_id': request.storeId,
      'items': request.items
          .map((i) => {
                'product_id': i.productId,
                'final_qty': i.finalQty,
                'override_reason': i.overrideReason,
              })
          .toList(),
    };
  }

  static ApprovalRequest fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return ApprovalRequest(
      storeId: (json['store_id'] as num).toInt(),
      items: rawItems.map((item) {
        final m = item as Map<String, dynamic>;
        return ApprovalItem(
          productId: (m['product_id'] as num).toInt(),
          finalQty: (m['final_qty'] as num).toInt(),
          overrideReason: m['override_reason'] as String?,
        );
      }).toList(),
    );
  }
}
