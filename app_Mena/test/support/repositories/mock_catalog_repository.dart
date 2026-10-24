import 'package:zerowaste_grocer/features/catalog/domain/models/product.dart';
import 'package:zerowaste_grocer/features/catalog/domain/repositories/catalog_repository.dart';
import '../datasources/catalog_mock_datasource.dart';

class MockCatalogRepository implements CatalogRepository {
  MockCatalogRepository({CatalogMockDataSource? dataSource})
      : _dataSource = dataSource ?? CatalogMockDataSource();

  final CatalogMockDataSource _dataSource;

  @override
  Future<List<Product>> getProducts(int storeId) => _dataSource.getProducts(storeId);

  @override
  Future<List<ProductBatch>> getBatches(int productId) => _dataSource.getBatches(productId);

  @override
  Future<void> submitAudit(int storeId, List<AuditEntry> entries) =>
      _dataSource.submitAudit(storeId, entries);
}
