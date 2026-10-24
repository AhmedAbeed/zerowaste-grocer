import '../../domain/models/product.dart';

class ProductModel {
  const ProductModel({
    required this.id,
    required this.sku,
    required this.name,
    required this.category,
    required this.unitCost,
    required this.unitPrice,
    required this.shelfLifeDays,
    required this.safetyStock,
    required this.currentStock,
  });

  factory ProductModel.fromJson(Map<String, dynamic> json) {
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

    return ProductModel(
      id: (json['id'] as num).toInt(),
      sku: json['sku'] as String? ?? '',
      name: json['name'] as String? ?? '',
      category: category,
      unitCost: (json['unit_cost'] as num?)?.toDouble() ?? 0.0,
      unitPrice: (json['unit_price'] as num?)?.toDouble() ?? 0.0,
      shelfLifeDays: (json['shelf_life_days'] as num?)?.toInt() ?? 5,
      safetyStock: (json['safety_stock'] as num?)?.toInt() ?? 5,
      currentStock: (json['current_stock'] as num?)?.toInt() ?? 0,
    );
  }

  final int id;
  final String sku;
  final String name;
  final ProductCategory category;
  final double unitCost;
  final double unitPrice;
  final int shelfLifeDays;
  final int safetyStock;
  final int currentStock;

  Product toDomain() {
    return Product(
      id: id,
      sku: sku,
      name: name,
      category: category,
      unitCost: unitCost,
      unitPrice: unitPrice,
      shelfLifeDays: shelfLifeDays,
      safetyStock: safetyStock,
      currentStock: currentStock,
    );
  }
}

class BatchModel {
  const BatchModel({
    required this.id,
    required this.productId,
    required this.receivedDate,
    required this.expirationDate,
    required this.remainingQty,
    required this.discountPct,
    this.daysToExpiry,
  });

  factory BatchModel.fromJson(Map<String, dynamic> json) {
    return BatchModel(
      id: json['id'] as String? ?? '',
      productId: (json['product_id'] as num).toInt(),
      receivedDate: DateTime.parse(json['received_date'] as String),
      expirationDate: DateTime.parse(json['expiration_date'] as String),
      remainingQty: (json['remaining_qty'] as num).toInt(),
      discountPct: (json['discount_pct'] as num?)?.toDouble() ?? 0.0,
      daysToExpiry: (json['days_to_expiry'] as num?)?.toInt(),
    );
  }

  final String id;
  final int productId;
  final DateTime receivedDate;
  final DateTime expirationDate;
  final int remainingQty;
  final double discountPct;
  final int? daysToExpiry;

  ProductBatch toDomain() {
    return ProductBatch(
      id: id,
      productId: productId,
      receivedDate: receivedDate,
      expirationDate: expirationDate,
      remainingQty: remainingQty,
      discountPct: discountPct,
      daysToExpiry: daysToExpiry,
    );
  }
}

class AuditEntryModel {
  static Map<String, dynamic> toJson(AuditEntry entry) {
    return {
      'product_id': entry.productId,
      'on_hand_qty': entry.onHandQty,
      'spoiled_qty': entry.spoiledQty,
    };
  }

  static AuditEntry fromJson(Map<String, dynamic> json) {
    return AuditEntry(
      productId: (json['product_id'] as num).toInt(),
      onHandQty: (json['on_hand_qty'] as num).toInt(),
      spoiledQty: (json['spoiled_qty'] as num).toInt(),
    );
  }
}
