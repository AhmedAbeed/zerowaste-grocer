import '../mock_database.dart';
import 'package:zerowaste_grocer/features/catalog/domain/models/product.dart';

class CatalogMockDataSource {
  final MockDatabase _db = MockDatabase.instance;

  Future<List<Product>> getProducts(int storeId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getProducts(storeId);
  }

  Future<List<ProductBatch>> getBatches(int productId) async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getBatches(productId);
  }

  Future<void> submitAudit(int storeId, List<AuditEntry> entries) async {
    await Future.delayed(const Duration(milliseconds: 400));
    _db.submitAudit(storeId, entries);
  }
}
