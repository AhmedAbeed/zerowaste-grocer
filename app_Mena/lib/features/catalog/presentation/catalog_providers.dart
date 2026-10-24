import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/dio_client.dart';
import '../../auth/presentation/auth_providers.dart';
import '../data/repositories/remote_catalog_repository.dart';
import '../domain/models/product.dart';
import '../domain/repositories/catalog_repository.dart';

/// Repository provider for Catalog
final catalogRepositoryProvider = Provider<CatalogRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return RemoteCatalogRepository(dio: dio);
});

/// Read call provider for products in the active store
final productsProvider = FutureProvider<List<Product>>((ref) async {
  final storeId = ref.watch(activeStoreIdProvider);
  final repository = ref.watch(catalogRepositoryProvider);
  return repository.getProducts(storeId);
});

/// Read call provider for batches associated with a specific product SKU
final productBatchesProvider = FutureProvider.family<List<ProductBatch>, int>((ref, productId) async {
  final repository = ref.watch(catalogRepositoryProvider);
  return repository.getBatches(productId);
});
