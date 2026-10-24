import 'package:dio/dio.dart';
import '../../domain/models/product.dart';
import '../models/catalog_models.dart';

class CatalogRemoteDataSource {
  const CatalogRemoteDataSource(this._dio);

  final Dio _dio;

  Future<List<Product>> getProducts(int storeId) async {
    final response = await _dio.get('/stores/$storeId/inventory');
    final data = response.data as Map<String, dynamic>;
    final items = data['items'] as List<dynamic>? ?? [];
    return items
        .map((item) => ProductModel.fromJson(item as Map<String, dynamic>).toDomain())
        .toList();
  }

  Future<List<ProductBatch>> getBatches(int productId) async {
    final response = await _dio.get('/products/$productId/batches');
    final list = response.data as List<dynamic>;
    return list
        .map((item) => BatchModel.fromJson(item as Map<String, dynamic>).toDomain())
        .toList();
  }

  Future<void> submitAudit(int storeId, List<AuditEntry> entries) async {
    await _dio.post(
      '/inventory/audit',
      data: {
        'store_id': storeId,
        'entries': entries.map((e) => AuditEntryModel.toJson(e)).toList(),
      },
    );
  }
}
