import '../models/product.dart';

abstract class CatalogRepository {
  Future<List<Product>> getProducts(int storeId);
  Future<List<ProductBatch>> getBatches(int productId);
  Future<void> submitAudit(int storeId, List<AuditEntry> entries);
}
