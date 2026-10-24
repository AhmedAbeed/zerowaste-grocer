import 'package:zerowaste_grocer/features/alerts/domain/models/spoilage_alert.dart';
import 'package:zerowaste_grocer/features/analytics/domain/models/waste_metrics.dart';
import 'package:zerowaste_grocer/features/auth/domain/models/app_user.dart';
import 'package:zerowaste_grocer/features/catalog/domain/models/product.dart';
import 'package:zerowaste_grocer/features/reorder/domain/models/recommendation.dart';

/// Singleton in-memory mock database that maintains consistent,
/// mutable state across all features for ZeroWaste Grocer.
class MockDatabase {
  MockDatabase._() {
    _initialize();
  }

  static final MockDatabase instance = MockDatabase._();

  // Stores
  late final List<Store> _stores;

  // Products per store: storeId -> List<Product>
  late final Map<int, List<Product>> _productsByStore;

  // Batches: productId -> List<ProductBatch>
  late final Map<int, List<ProductBatch>> _batchesByProduct;

  // Predicted demand per product for batch alert evaluation
  late final Map<int, int> _productBatchPredictedDemand;

  // Recommendations per store: storeId -> List<Recommendation>
  late final Map<int, List<Recommendation>> _recommendationsByStore;

  // Alerts per store: storeId -> List<SpoilageAlert>
  late final Map<int, List<SpoilageAlert>> _alertsByStore;

  // Sales points (30 days)
  late final Map<int, List<SalesPoint>> _salesPointsByStore;

  // Category waste units: storeId -> Map<ProductCategory, int>
  late final Map<int, Map<ProductCategory, int>> _categoryWasteByStore;

  void _initialize() {
    _stores = const [
      Store(
        id: 1,
        name: 'Metro Downtown Branch',
        location: '101 Grand Ave, Central Metro',
      ),
      Store(
        id: 2,
        name: 'Suburban Supercenter',
        location: '450 Valley Blvd, Westside Suburbs',
      ),
      Store(
        id: 3,
        name: 'Harbor Organic Market',
        location: '72 Ocean View Dr, Marina Bay',
      ),
    ];

    // Master list of 15 products across 4 categories (Produce, Dairy, Bakery, Butchery)
    final masterProducts = <Product>[
      // Produce (4 products)
      const Product(
        id: 1,
        sku: 'PRD-AVO-01',
        name: 'Organic Hass Avocados',
        category: ProductCategory.produce,
        unitCost: 1.20,
        unitPrice: 2.49,
        shelfLifeDays: 5,
        safetyStock: 15,
        currentStock: 28,
      ),
      const Product(
        id: 2,
        sku: 'PRD-SPN-02',
        name: 'Baby Spinach 200g',
        category: ProductCategory.produce,
        unitCost: 1.10,
        unitPrice: 2.99,
        shelfLifeDays: 6,
        safetyStock: 12,
        currentStock: 18,
      ),
      const Product(
        id: 3,
        sku: 'PRD-APL-03',
        name: 'Honeycrisp Apples 1kg',
        category: ProductCategory.produce,
        unitCost: 1.50,
        unitPrice: 3.49,
        shelfLifeDays: 14,
        safetyStock: 20,
        currentStock: 35,
      ),
      const Product(
        id: 4,
        sku: 'PRD-TOM-04',
        name: 'Roma Tomatoes 500g',
        category: ProductCategory.produce,
        unitCost: 0.90,
        unitPrice: 1.99,
        shelfLifeDays: 7,
        safetyStock: 14,
        currentStock: 24,
      ),

      // Dairy (4 products)
      const Product(
        id: 5,
        sku: 'DAY-MLK-05',
        name: 'Whole Milk 1 Gallon',
        category: ProductCategory.dairy,
        unitCost: 2.10,
        unitPrice: 3.89,
        shelfLifeDays: 10,
        safetyStock: 15,
        currentStock: 25,
      ),
      const Product(
        id: 6,
        sku: 'DAY-YOG-06',
        name: 'Greek Yogurt Plain 500g',
        category: ProductCategory.dairy,
        unitCost: 1.80,
        unitPrice: 3.49,
        shelfLifeDays: 12,
        safetyStock: 12,
        currentStock: 20,
      ),
      const Product(
        id: 7,
        sku: 'DAY-BUT-07',
        name: 'Organic Salted Butter 250g',
        category: ProductCategory.dairy,
        unitCost: 2.50,
        unitPrice: 4.99,
        shelfLifeDays: 30,
        safetyStock: 10,
        currentStock: 16,
      ),
      const Product(
        id: 8,
        sku: 'DAY-CHD-08',
        name: 'Sharp Cheddar Block 200g',
        category: ProductCategory.dairy,
        unitCost: 3.20,
        unitPrice: 5.99,
        shelfLifeDays: 45,
        safetyStock: 8,
        currentStock: 14,
      ),

      // Bakery (4 products)
      const Product(
        id: 9,
        sku: 'BAK-SRD-09',
        name: 'Artisanal Sourdough Loaf',
        category: ProductCategory.bakery,
        unitCost: 1.50,
        unitPrice: 4.49,
        shelfLifeDays: 3,
        safetyStock: 8,
        currentStock: 12,
      ),
      const Product(
        id: 10,
        sku: 'BAK-CRS-10',
        name: 'Butter Croissants 4-Pack',
        category: ProductCategory.bakery,
        unitCost: 2.20,
        unitPrice: 4.99,
        shelfLifeDays: 2,
        safetyStock: 6,
        currentStock: 10,
      ),
      const Product(
        id: 11,
        sku: 'BAK-WGB-11',
        name: 'Whole Grain Sandwich Bread',
        category: ProductCategory.bakery,
        unitCost: 1.40,
        unitPrice: 3.79,
        shelfLifeDays: 5,
        safetyStock: 10,
        currentStock: 16,
      ),
      const Product(
        id: 12,
        sku: 'BAK-BRC-12',
        name: 'Cinnamon Brioche Buns',
        category: ProductCategory.bakery,
        unitCost: 1.80,
        unitPrice: 4.29,
        shelfLifeDays: 3,
        safetyStock: 6,
        currentStock: 9,
      ),

      // Butchery (3 products)
      const Product(
        id: 13,
        sku: 'BTC-RBX-13',
        name: 'Grass-fed Ribeye Steak 350g',
        category: ProductCategory.butchery,
        unitCost: 8.50,
        unitPrice: 16.99,
        shelfLifeDays: 4,
        safetyStock: 6,
        currentStock: 11,
      ),
      const Product(
        id: 14,
        sku: 'BTC-CHK-14',
        name: 'Organic Chicken Breast 500g',
        category: ProductCategory.butchery,
        unitCost: 4.20,
        unitPrice: 8.99,
        shelfLifeDays: 4,
        safetyStock: 10,
        currentStock: 18,
      ),
      const Product(
        id: 15,
        sku: 'BTC-GBF-15',
        name: 'Lean Ground Beef 90/10 500g',
        category: ProductCategory.butchery,
        unitCost: 5.00,
        unitPrice: 9.49,
        shelfLifeDays: 3,
        safetyStock: 8,
        currentStock: 14,
      ),
    ];

    // Seed products for each store
    _productsByStore = {
      1: List<Product>.from(masterProducts),
      2: masterProducts.map((p) => p.copyWith(currentStock: (p.currentStock * 1.2).round())).toList(),
      3: masterProducts.map((p) => p.copyWith(currentStock: (p.currentStock * 0.9).round())).toList(),
    };

    final now = DateTime.now();

    // Batches with a mix of expiring within 2 days and fresh inventory
    _batchesByProduct = {
      1: [
        ProductBatch(
          id: 'B-AVO-101',
          productId: 1,
          receivedDate: now.subtract(const Duration(days: 1)),
          expirationDate: now.add(const Duration(days: 4)),
          remainingQty: 18,
          discountPct: 0.0,
        ),
        ProductBatch(
          id: 'B-AVO-102',
          productId: 1,
          receivedDate: now.subtract(const Duration(days: 2)),
          expirationDate: now.add(const Duration(days: 3)),
          remainingQty: 10,
          discountPct: 0.0,
        ),
      ],
      // Product 2: Expiring in 1 day with surplus (remaining 10, predicted demand 4) -> Alert candidate!
      2: [
        ProductBatch(
          id: 'B-SPN-201',
          productId: 2,
          receivedDate: now.subtract(const Duration(days: 4)),
          expirationDate: now.add(const Duration(days: 1)),
          remainingQty: 10,
          discountPct: 0.0,
        ),
        ProductBatch(
          id: 'B-SPN-202',
          productId: 2,
          receivedDate: now.subtract(const Duration(days: 1)),
          expirationDate: now.add(const Duration(days: 5)),
          remainingQty: 8,
          discountPct: 0.0,
        ),
      ],
      3: [
        ProductBatch(
          id: 'B-APL-301',
          productId: 3,
          receivedDate: now.subtract(const Duration(days: 2)),
          expirationDate: now.add(const Duration(days: 12)),
          remainingQty: 35,
          discountPct: 0.0,
        ),
      ],
      4: [
        ProductBatch(
          id: 'B-TOM-401',
          productId: 4,
          receivedDate: now.subtract(const Duration(days: 3)),
          expirationDate: now.add(const Duration(days: 4)),
          remainingQty: 24,
          discountPct: 0.0,
        ),
      ],
      5: [
        ProductBatch(
          id: 'B-MLK-501',
          productId: 5,
          receivedDate: now.subtract(const Duration(days: 3)),
          expirationDate: now.add(const Duration(days: 7)),
          remainingQty: 25,
          discountPct: 0.0,
        ),
      ],
      6: [
        ProductBatch(
          id: 'B-YOG-601',
          productId: 6,
          receivedDate: now.subtract(const Duration(days: 4)),
          expirationDate: now.add(const Duration(days: 8)),
          remainingQty: 20,
          discountPct: 0.0,
        ),
      ],
      7: [
        ProductBatch(
          id: 'B-BUT-701',
          productId: 7,
          receivedDate: now.subtract(const Duration(days: 5)),
          expirationDate: now.add(const Duration(days: 25)),
          remainingQty: 16,
          discountPct: 0.0,
        ),
      ],
      8: [
        ProductBatch(
          id: 'B-CHD-801',
          productId: 8,
          receivedDate: now.subtract(const Duration(days: 10)),
          expirationDate: now.add(const Duration(days: 35)),
          remainingQty: 14,
          discountPct: 0.0,
        ),
      ],
      // Product 9: Expiring in 2 days with surplus (remaining 6, predicted demand 2) -> Alert candidate!
      9: [
        ProductBatch(
          id: 'B-SRD-901',
          productId: 9,
          receivedDate: now.subtract(const Duration(days: 1)),
          expirationDate: now.add(const Duration(days: 2)),
          remainingQty: 6,
          discountPct: 0.0,
        ),
        ProductBatch(
          id: 'B-SRD-902',
          productId: 9,
          receivedDate: now,
          expirationDate: now.add(const Duration(days: 3)),
          remainingQty: 6,
          discountPct: 0.0,
        ),
      ],
      // Product 10: Expiring in 1 day with surplus (remaining 7, predicted demand 3) -> Alert candidate!
      10: [
        ProductBatch(
          id: 'B-CRS-1001',
          productId: 10,
          receivedDate: now.subtract(const Duration(days: 1)),
          expirationDate: now.add(const Duration(days: 1)),
          remainingQty: 7,
          discountPct: 0.0,
        ),
        ProductBatch(
          id: 'B-CRS-1002',
          productId: 10,
          receivedDate: now,
          expirationDate: now.add(const Duration(days: 2)),
          remainingQty: 3,
          discountPct: 0.0,
        ),
      ],
      11: [
        ProductBatch(
          id: 'B-WGB-1101',
          productId: 11,
          receivedDate: now.subtract(const Duration(days: 1)),
          expirationDate: now.add(const Duration(days: 4)),
          remainingQty: 16,
          discountPct: 0.0,
        ),
      ],
      12: [
        ProductBatch(
          id: 'B-BRC-1201',
          productId: 12,
          receivedDate: now.subtract(const Duration(days: 1)),
          expirationDate: now.add(const Duration(days: 3)),
          remainingQty: 9,
          discountPct: 0.0,
        ),
      ],
      13: [
        ProductBatch(
          id: 'B-RBX-1301',
          productId: 13,
          receivedDate: now.subtract(const Duration(days: 1)),
          expirationDate: now.add(const Duration(days: 3)),
          remainingQty: 11,
          discountPct: 0.0,
        ),
      ],
      // Product 14: Expiring in 2 days with surplus (remaining 8, predicted demand 3) -> Alert candidate!
      14: [
        ProductBatch(
          id: 'B-CHK-1401',
          productId: 14,
          receivedDate: now.subtract(const Duration(days: 2)),
          expirationDate: now.add(const Duration(days: 2)),
          remainingQty: 8,
          discountPct: 0.0,
        ),
        ProductBatch(
          id: 'B-CHK-1402',
          productId: 14,
          receivedDate: now,
          expirationDate: now.add(const Duration(days: 4)),
          remainingQty: 10,
          discountPct: 0.0,
        ),
      ],
      15: [
        ProductBatch(
          id: 'B-GBF-1501',
          productId: 15,
          receivedDate: now.subtract(const Duration(days: 1)),
          expirationDate: now.add(const Duration(days: 3)),
          remainingQty: 14,
          discountPct: 0.0,
        ),
      ],
    };

    // Predicted demand for batch surplus calculation
    _productBatchPredictedDemand = {
      2: 4,
      9: 2,
      10: 3,
      14: 3,
    };

    // Derive initial alerts from batches where daysToExpiry <= 2 AND predictedDemand < remainingQty
    _alertsByStore = {
      1: _deriveAlertsForStore(1),
      2: _deriveAlertsForStore(2),
      3: _deriveAlertsForStore(3),
    };

    // 10 recommendations per store with believable XAI reasons and drivers
    _recommendationsByStore = {
      1: _buildRecommendationsForStore(1),
      2: _buildRecommendationsForStore(2),
      3: _buildRecommendationsForStore(3),
    };

    // 30 days of sales points
    _salesPointsByStore = {
      1: _generateSalesSeries(base: 3800.0),
      2: _generateSalesSeries(base: 4500.0),
      3: _generateSalesSeries(base: 3200.0),
    };

    // Category waste units
    _categoryWasteByStore = {
      1: {
        ProductCategory.produce: 42,
        ProductCategory.dairy: 28,
        ProductCategory.bakery: 35,
        ProductCategory.butchery: 16,
      },
      2: {
        ProductCategory.produce: 55,
        ProductCategory.dairy: 34,
        ProductCategory.bakery: 40,
        ProductCategory.butchery: 22,
      },
      3: {
        ProductCategory.produce: 36,
        ProductCategory.dairy: 22,
        ProductCategory.bakery: 28,
        ProductCategory.butchery: 12,
      },
    };
  }

  // --- Alert Derivation ---
  List<SpoilageAlert> _deriveAlertsForStore(int storeId) {
    final alerts = <SpoilageAlert>[];
    final now = DateTime.now();

    for (final entry in _batchesByProduct.entries) {
      final productId = entry.key;
      final batches = entry.value;
      final predictedDemand = _productBatchPredictedDemand[productId] ?? 999;

      for (final batch in batches) {
        final diffDays = batch.expirationDate.difference(now).inDays;
        if (diffDays <= 2 && batch.remainingQty > predictedDemand) {
          final product = _findProduct(storeId, productId);
          final discount = diffDays <= 1 ? 0.40 : 0.25;

          alerts.add(
            SpoilageAlert(
              id: 'ALT-$storeId-${batch.id}',
              batchId: batch.id,
              productId: productId,
              productName: product?.name ?? 'Product #$productId',
              daysToExpiry: diffDays < 0 ? 0 : diffDays,
              remainingQty: batch.remainingQty,
              predictedDemand: predictedDemand,
              suggestedDiscountPct: discount,
              status: AlertStatus.open,
            ),
          );
        }
      }
    }
    return alerts;
  }

  // --- Recommendation Construction (10 items per store) ---
  List<Recommendation> _buildRecommendationsForStore(int storeId) {
    return [
      Recommendation(
        productId: 1,
        productName: 'Organic Hass Avocados',
        category: ProductCategory.produce,
        currentStock: _findProduct(storeId, 1)?.currentStock ?? 28,
        safetyStock: 15,
        predictedDemand: 46,
        recommendedQty: 33,
        approvedQty: 33,
        status: RecommendationStatus.pending,
        xaiReason: 'Sunny weekend forecast expected to drive guacamole and brunch demand (+35%).',
        xaiDrivers: const [
          XaiDriver(label: 'Weekend Weather', impactPct: 22.0),
          XaiDriver(label: 'Foot Traffic Surge', impactPct: 13.0),
        ],
      ),
      Recommendation(
        productId: 2,
        productName: 'Baby Spinach 200g',
        category: ProductCategory.produce,
        currentStock: _findProduct(storeId, 2)?.currentStock ?? 18,
        safetyStock: 12,
        predictedDemand: 28,
        recommendedQty: 22,
        approvedQty: 22,
        status: RecommendationStatus.pending,
        xaiReason: 'Midweek health & salad trend with high turnover history.',
        xaiDrivers: const [
          XaiDriver(label: 'Health Trend Promotion', impactPct: 16.0),
          XaiDriver(label: 'Historical Sell-Through', impactPct: 12.0),
        ],
      ),
      Recommendation(
        productId: 3,
        productName: 'Honeycrisp Apples 1kg',
        category: ProductCategory.produce,
        currentStock: _findProduct(storeId, 3)?.currentStock ?? 35,
        safetyStock: 20,
        predictedDemand: 52,
        recommendedQty: 37,
        approvedQty: 37,
        status: RecommendationStatus.pending,
        xaiReason: 'Autumn harvest seasonal peak and school lunchbox demand surge.',
        xaiDrivers: const [
          XaiDriver(label: 'Harvest Seasonality', impactPct: 24.0),
          XaiDriver(label: 'Family Basket Size', impactPct: 10.0),
        ],
      ),
      Recommendation(
        productId: 5,
        productName: 'Whole Milk 1 Gallon',
        category: ProductCategory.dairy,
        currentStock: _findProduct(storeId, 5)?.currentStock ?? 25,
        safetyStock: 15,
        predictedDemand: 54,
        recommendedQty: 44,
        approvedQty: 44,
        status: RecommendationStatus.pending,
        xaiReason: 'Bi-weekly residential restocking cycle with minimal demand elasticity.',
        xaiDrivers: const [
          XaiDriver(label: 'Household Restock Cycle', impactPct: 20.0),
          XaiDriver(label: 'Baseline Stability', impactPct: 14.0),
        ],
      ),
      Recommendation(
        productId: 6,
        productName: 'Greek Yogurt Plain 500g',
        category: ProductCategory.dairy,
        currentStock: _findProduct(storeId, 6)?.currentStock ?? 20,
        safetyStock: 12,
        predictedDemand: 36,
        recommendedQty: 28,
        approvedQty: 28,
        status: RecommendationStatus.pending,
        xaiReason: 'Breakfast pantry demand climbing ahead of upcoming long weekend.',
        xaiDrivers: const [
          XaiDriver(label: 'Breakfast Staples Surge', impactPct: 18.0),
          XaiDriver(label: 'Long Weekend Multiplier', impactPct: 9.0),
        ],
      ),
      Recommendation(
        productId: 9,
        productName: 'Artisanal Sourdough Loaf',
        category: ProductCategory.bakery,
        currentStock: _findProduct(storeId, 9)?.currentStock ?? 12,
        safetyStock: 8,
        predictedDemand: 28,
        recommendedQty: 24,
        approvedQty: 24,
        status: RecommendationStatus.pending,
        xaiReason: 'Morning commuter foot traffic and rain forecast stimulating bakery purchases.',
        xaiDrivers: const [
          XaiDriver(label: 'Commuter Morning Peak', impactPct: 19.0),
          XaiDriver(label: 'Rainfall Comfort Multiplier', impactPct: 11.0),
        ],
      ),
      Recommendation(
        productId: 10,
        productName: 'Butter Croissants 4-Pack',
        category: ProductCategory.bakery,
        currentStock: _findProduct(storeId, 10)?.currentStock ?? 10,
        safetyStock: 6,
        predictedDemand: 22,
        recommendedQty: 18,
        approvedQty: 18,
        status: RecommendationStatus.pending,
        xaiReason: 'Saturday brunch crowd driving quick early morning stock-out risk.',
        xaiDrivers: const [
          XaiDriver(label: 'Weekend Brunch Traffic', impactPct: 26.0),
          XaiDriver(label: 'Coffee Pairing Effect', impactPct: 14.0),
        ],
      ),
      Recommendation(
        productId: 13,
        productName: 'Grass-fed Ribeye Steak 350g',
        category: ProductCategory.butchery,
        currentStock: _findProduct(storeId, 13)?.currentStock ?? 11,
        safetyStock: 6,
        predictedDemand: 25,
        recommendedQty: 20,
        approvedQty: 20,
        status: RecommendationStatus.pending,
        xaiReason: 'Sunny outdoor barbecue conditions forecasted across the metro area.',
        xaiDrivers: const [
          XaiDriver(label: 'Outdoor Grilling Weather', impactPct: 30.0),
          XaiDriver(label: 'Payday Weekend Index', impactPct: 15.0),
        ],
      ),
      Recommendation(
        productId: 14,
        productName: 'Organic Chicken Breast 500g',
        category: ProductCategory.butchery,
        currentStock: _findProduct(storeId, 14)?.currentStock ?? 18,
        safetyStock: 10,
        predictedDemand: 40,
        recommendedQty: 32,
        approvedQty: 32,
        status: RecommendationStatus.pending,
        xaiReason: 'High weekly meal-prep staple demand following fitness gym partnership promo.',
        xaiDrivers: const [
          XaiDriver(label: 'Local Event Promotion', impactPct: 20.0),
          XaiDriver(label: 'Meal-Prep Baseline', impactPct: 12.0),
        ],
      ),
      Recommendation(
        productId: 15,
        productName: 'Lean Ground Beef 90/10 500g',
        category: ProductCategory.butchery,
        currentStock: _findProduct(storeId, 15)?.currentStock ?? 14,
        safetyStock: 8,
        predictedDemand: 32,
        recommendedQty: 26,
        approvedQty: 26,
        status: RecommendationStatus.pending,
        xaiReason: 'Aisle 3 taco/pasta discount promotion stimulating cross-merchandised ground beef.',
        xaiDrivers: const [
          XaiDriver(label: 'Cross-Category Promo', impactPct: 21.0),
          XaiDriver(label: 'Taco Tuesday Baseline', impactPct: 11.0),
        ],
      ),
    ];
  }

  List<SalesPoint> _generateSalesSeries({required double base}) {
    final now = DateTime.now();
    final points = <SalesPoint>[];

    for (int i = 29; i >= 0; i--) {
      final date = now.subtract(Duration(days: i));
      final dayOfWeek = date.weekday;
      final isWeekend = dayOfWeek == DateTime.saturday || dayOfWeek == DateTime.sunday;
      final weekendMultiplier = isWeekend ? 1.35 : 1.0;
      final variation = (i % 5 - 2) * 80.0;

      final predicted = (base * weekendMultiplier) + variation;
      final actual = predicted + ((i % 3 - 1) * 65.0);

      points.add(
        SalesPoint(
          date: date,
          actual: double.parse(actual.toStringAsFixed(2)),
          predicted: double.parse(predicted.toStringAsFixed(2)),
        ),
      );
    }
    return points;
  }

  Product? _findProduct(int storeId, int productId) {
    final list = _productsByStore[storeId] ?? _productsByStore[1] ?? [];
    for (final p in list) {
      if (p.id == productId) return p;
    }
    return null;
  }

  // --- Public Read APIs ---

  List<Store> getStores() => List.unmodifiable(_stores);

  List<Product> getProducts(int storeId) {
    return List.unmodifiable(_productsByStore[storeId] ?? _productsByStore[1] ?? []);
  }

  List<ProductBatch> getBatches(int productId) {
    return List.unmodifiable(_batchesByProduct[productId] ?? []);
  }

  List<Recommendation> getRecommendations(int storeId, [DateTime? targetDate]) {
    return List.unmodifiable(_recommendationsByStore[storeId] ?? _recommendationsByStore[1] ?? []);
  }

  List<SpoilageAlert> getAlerts(int storeId) {
    return List.unmodifiable(_alertsByStore[storeId] ?? _alertsByStore[1] ?? []);
  }

  List<SalesPoint> getSalesSeries(int storeId) {
    return List.unmodifiable(_salesPointsByStore[storeId] ?? _salesPointsByStore[1] ?? []);
  }

  List<CategoryWaste> getCategoryWaste(int storeId) {
    final wasteMap = _categoryWasteByStore[storeId] ?? _categoryWasteByStore[1] ?? {};
    return wasteMap.entries
        .map((e) => CategoryWaste(category: e.key, units: e.value))
        .toList(growable: false);
  }

  /// Dashboard metrics dynamically computed from current mock state
  WasteMetrics getMetrics(int storeId) {
    final alerts = _alertsByStore[storeId] ?? _alertsByStore[1] ?? [];
    final recommendations = _recommendationsByStore[storeId] ?? _recommendationsByStore[1] ?? [];

    // Units at risk and exposure from active open alerts
    int unitsAtRisk = 0;
    double projectedExposure = 0.0;

    for (final alert in alerts) {
      if (alert.status == AlertStatus.open) {
        unitsAtRisk += alert.remainingQty;
        final product = _findProduct(storeId, alert.productId);
        final cost = product?.unitCost ?? 2.0;
        projectedExposure += (alert.remainingQty * cost);
      }
    }

    // Pending orders count from recommendations
    final pendingOrders = recommendations
        .where((r) => r.status == RecommendationStatus.pending)
        .length;

    // Computed sustainability metrics
    final acceptedUnits = alerts
        .where((a) => a.status == AlertStatus.accepted)
        .fold<int>(0, (sum, a) => sum + a.remainingQty);
    const kgPerUnitAssumption = 0.35; // assumption, not measured
    final kgSaved = acceptedUnits * kgPerUnitAssumption;
    final co2Saved = kgSaved * 2.5; // assumption

    return WasteMetrics(
      unitsAtRisk: unitsAtRisk,
      projectedExposure: double.parse(projectedExposure.toStringAsFixed(2)),
      pendingOrders: pendingOrders,
      kgSaved: double.parse(kgSaved.toStringAsFixed(1)),
      co2Saved: double.parse(co2Saved.toStringAsFixed(1)),
    );
  }

  // --- Public Mutation APIs (mutates state in memory) ---

  void submitAudit(int storeId, List<AuditEntry> entries) {
    final currentProducts = _productsByStore[storeId] ?? [];
    final updatedList = <Product>[];

    for (final product in currentProducts) {
      final entry = entries.where((e) => e.productId == product.id).firstOrNull;
      if (entry != null) {
        updatedList.add(product.copyWith(currentStock: entry.onHandQty));
        // Add spoiled units to category waste
        if (entry.spoiledQty > 0) {
          final wasteMap = _categoryWasteByStore[storeId];
          if (wasteMap != null) {
            wasteMap[product.category] = (wasteMap[product.category] ?? 0) + entry.spoiledQty;
          }
        }
      } else {
        updatedList.add(product);
      }
    }
    _productsByStore[storeId] = updatedList;
  }

  bool approveRecommendations(ApprovalRequest request) {
    final currentList = _recommendationsByStore[request.storeId] ?? [];
    final updatedList = <Recommendation>[];

    for (final rec in currentList) {
      final item = request.items.where((i) => i.productId == rec.productId).firstOrNull;
      if (item != null) {
        final isOverridden = item.overrideReason != null && item.overrideReason!.isNotEmpty;
        updatedList.add(
          rec.copyWith(
            approvedQty: item.finalQty,
            status: isOverridden ? RecommendationStatus.overridden : RecommendationStatus.approved,
          ),
        );
      } else {
        updatedList.add(rec);
      }
    }
    _recommendationsByStore[request.storeId] = updatedList;
    return true;
  }

  void resetRecommendations() {
    for (final storeId in _recommendationsByStore.keys) {
      _recommendationsByStore[storeId] = _recommendationsByStore[storeId]!
          .map((r) => r.copyWith(status: RecommendationStatus.pending))
          .toList();
    }
  }

  void acceptMarkdown(String alertId) {
    for (final storeId in _alertsByStore.keys) {
      final list = _alertsByStore[storeId] ?? [];
      final index = list.indexWhere((a) => a.id == alertId);
      if (index != -1) {
        final alert = list[index];
        list[index] = alert.copyWith(
          status: AlertStatus.accepted,
          appliedDiscountPct: alert.suggestedDiscountPct,
        );

        // Apply discount to the matching product batch
        final batches = _batchesByProduct[alert.productId] ?? [];
        for (int b = 0; b < batches.length; b++) {
          if (batches[b].expirationDate.difference(DateTime.now()).inDays <= 2) {
            batches[b] = batches[b].copyWith(discountPct: alert.suggestedDiscountPct);
          }
        }
        break;
      }
    }
  }

  void dismissAlert(String alertId) {
    for (final storeId in _alertsByStore.keys) {
      final list = _alertsByStore[storeId] ?? [];
      list.removeWhere((a) => a.id == alertId || a.batchId == alertId);
    }
  }
}
