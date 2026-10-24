import 'package:dio/dio.dart';
import '../../../../core/offline/offline_queue_service.dart';
import '../../domain/models/product.dart';
import '../../domain/repositories/catalog_repository.dart';
import '../datasources/catalog_remote_datasource.dart';

class RemoteCatalogRepository implements CatalogRepository {
  RemoteCatalogRepository({CatalogRemoteDataSource? remoteDataSource, Dio? dio})
      : _remoteDataSource = remoteDataSource ?? CatalogRemoteDataSource(dio ?? Dio());

  final CatalogRemoteDataSource _remoteDataSource;

  @override
  Future<List<Product>> getProducts(int storeId) {
    return _remoteDataSource.getProducts(storeId);
  }

  @override
  Future<List<ProductBatch>> getBatches(int productId) {
    return _remoteDataSource.getBatches(productId);
  }

  @override
  Future<void> submitAudit(int storeId, List<AuditEntry> entries) async {
    try {
      await _remoteDataSource.submitAudit(storeId, entries);
    } on DioException {
      // Buffer offline if network issue occurs
      await OfflineQueueService.enqueueAudit(storeId, entries);
    } catch (_) {
      await OfflineQueueService.enqueueAudit(storeId, entries);
    }
  }
}
