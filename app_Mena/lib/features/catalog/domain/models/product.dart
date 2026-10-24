/// Perishable product categories handled by ZeroWaste Grocer.
enum ProductCategory {
  produce,
  dairy,
  bakery,
  butchery,
}

/// Core product entity representing a perishable SKU in a grocery store.
class Product {
  const Product({
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

  final int id;
  final String sku;
  final String name;
  final ProductCategory category;
  final double unitCost;
  final double unitPrice;
  final int shelfLifeDays;
  final int safetyStock;
  final int currentStock;

  Product copyWith({
    int? id,
    String? sku,
    String? name,
    ProductCategory? category,
    double? unitCost,
    double? unitPrice,
    int? shelfLifeDays,
    int? safetyStock,
    int? currentStock,
  }) {
    return Product(
      id: id ?? this.id,
      sku: sku ?? this.sku,
      name: name ?? this.name,
      category: category ?? this.category,
      unitCost: unitCost ?? this.unitCost,
      unitPrice: unitPrice ?? this.unitPrice,
      shelfLifeDays: shelfLifeDays ?? this.shelfLifeDays,
      safetyStock: safetyStock ?? this.safetyStock,
      currentStock: currentStock ?? this.currentStock,
    );
  }
}

/// Represents an incoming inventory batch with specific receiving and expiry dates.
class ProductBatch {
  const ProductBatch({
    required this.id,
    required this.productId,
    required this.receivedDate,
    required this.expirationDate,
    required this.remainingQty,
    required this.discountPct,
    this.daysToExpiry,
  });

  final String id;
  final int productId;
  final DateTime receivedDate;
  final DateTime expirationDate;
  final int remainingQty;
  final double discountPct;
  final int? daysToExpiry;

  ProductBatch copyWith({
    String? id,
    int? productId,
    DateTime? receivedDate,
    DateTime? expirationDate,
    int? remainingQty,
    double? discountPct,
    int? daysToExpiry,
  }) {
    return ProductBatch(
      id: id ?? this.id,
      productId: productId ?? this.productId,
      receivedDate: receivedDate ?? this.receivedDate,
      expirationDate: expirationDate ?? this.expirationDate,
      remainingQty: remainingQty ?? this.remainingQty,
      discountPct: discountPct ?? this.discountPct,
      daysToExpiry: daysToExpiry ?? this.daysToExpiry,
    );
  }
}

/// Closing audit entry recording physical on-hand stock and discarded spoiled units.
class AuditEntry {
  const AuditEntry({
    required this.productId,
    required this.onHandQty,
    required this.spoiledQty,
  });

  final int productId;
  final int onHandQty;
  final int spoiledQty;
}
