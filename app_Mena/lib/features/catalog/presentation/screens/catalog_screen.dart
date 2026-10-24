import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../auth/presentation/auth_providers.dart';
import '../../domain/models/product.dart';
import '../catalog_providers.dart';
import '../widgets/closing_audit_dialog.dart';
import '../widgets/product_card.dart';

class CatalogScreen extends ConsumerStatefulWidget {
  const CatalogScreen({super.key});

  @override
  ConsumerState<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends ConsumerState<CatalogScreen> {
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounceTimer;
  String _searchQuery = '';
  ProductCategory? _selectedCategory; // null = 'All'
  bool _sortByExpiryUrgency = false;

  @override
  void dispose() {
    _searchController.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String value) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      if (mounted) {
        setState(() {
          _searchQuery = value.trim();
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final productsAsync = ref.watch(productsProvider);
    final activeStoreId = ref.watch(activeStoreIdProvider);

    return Scaffold(
      
      body: productsAsync.when(
        data: (products) {
          // Filter products by selected category and search query
          final filtered = products.where((p) {
            final matchesCategory =
                _selectedCategory == null || p.category == _selectedCategory;
            final matchesSearch = _searchQuery.isEmpty ||
                p.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
                p.sku.toLowerCase().contains(_searchQuery.toLowerCase());
            return matchesCategory && matchesSearch;
          }).toList();

          // Sort by shelf life if expiry urgency toggle is enabled
          if (_sortByExpiryUrgency) {
            filtered.sort((a, b) => a.shelfLifeDays.compareTo(b.shelfLifeDays));
          }

          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 900),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
              // Top Category Chips Bar
              Container(
                color: context.surfaceColor,
                padding: const EdgeInsets.symmetric(vertical: 10),
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    children: [
                      _buildCategoryChip(label: 'All', category: null),
                      SizedBox(width: 8),
                      _buildCategoryChip(
                        label: 'Produce',
                        category: ProductCategory.produce,
                      ),
                      SizedBox(width: 8),
                      _buildCategoryChip(
                        label: 'Dairy',
                        category: ProductCategory.dairy,
                      ),
                      SizedBox(width: 8),
                      _buildCategoryChip(
                        label: 'Bakery',
                        category: ProductCategory.bakery,
                      ),
                      SizedBox(width: 8),
                      _buildCategoryChip(
                        label: 'Butchery',
                        category: ProductCategory.butchery,
                      ),
                    ],
                  ),
                ),
              ),

              // Search Bar & Sort Toggle Row
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _searchController,
                        onChanged: _onSearchChanged,
                        decoration: InputDecoration(
                          hintText: 'Search perishable products...',
                          prefixIcon: Icon(
                            Icons.search_rounded,
                            color: context.primaryBrand,
                          ),
                          suffixIcon: _searchController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear_rounded, size: 18),
                                  onPressed: () {
                                    _searchController.clear();
                                    _onSearchChanged('');
                                  },
                                )
                              : null,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 14,
                            vertical: 10,
                          ),
                          filled: true,
                          fillColor: context.surfaceColor,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Tooltip(
                      message: _sortByExpiryUrgency
                          ? 'Sorting: Expiry Urgency'
                          : 'Sort by Expiry Urgency',
                      child: Material(
                        color: _sortByExpiryUrgency
                            ? AppColors.forestGreen
                            : Colors.white,
                        borderRadius: BorderRadius.circular(8),
                        elevation: 1,
                        child: InkWell(
                          borderRadius: BorderRadius.circular(8),
                          onTap: () {
                            setState(() {
                              _sortByExpiryUrgency = !_sortByExpiryUrgency;
                            });
                          },
                          child: Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(
                                color: _sortByExpiryUrgency
                                    ? AppColors.forestGreen
                                    : AppColors.divider,
                              ),
                            ),
                            child: Icon(
                              Icons.hourglass_bottom_rounded,
                              size: 20,
                              color: _sortByExpiryUrgency
                                  ? Colors.white
                                  : AppColors.textSecondary,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              // Product Count & Active Filter Indicator
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 4),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '${filtered.length} products available',
                      style: TextStyle(
                        fontSize: 12,
                        color: context.textSecondaryColor,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (_sortByExpiryUrgency)
                      Text(
                        'Sorted by urgency',
                        style: TextStyle(
                          fontSize: 11,
                          color: context.primaryBrand,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                  ],
                ),
              ),

              // Products List
              Expanded(
                child: filtered.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.inventory_2_outlined,
                              size: 48,
                              color: context.textSecondaryColor,
                            ),
                            SizedBox(height: 12),
                            Text(
                              'No products match your criteria',
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                                color: context.textColor,
                              ),
                            ),
                            SizedBox(height: 6),
                            Text(
                              _searchQuery.isNotEmpty
                                  ? 'Try adjusting your search terms'
                                  : 'Select another category filter',
                              style: TextStyle(
                                fontSize: 13,
                                color: context.textSecondaryColor,
                              ),
                            ),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        color: context.primaryBrand,
                        onRefresh: () async {
                          return ref.refresh(productsProvider.future);
                        },
                        child: ListView.builder(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.only(top: 4, bottom: 84),
                          itemCount: filtered.length,
                          itemBuilder: (context, index) {
                            return ProductCard(product: filtered[index]);
                          },
                        ),
                      ),
              ),
            ],
          ),
        ),
      );
    },
        loading: () => Center(
          child: CircularProgressIndicator(color: AppColors.forestGreen),
        ),
        error: (error, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline_rounded,
                size: 48,
                color: context.criticalColor,
              ),
              const SizedBox(height: 12),
              Text('Failed to load products: $error'),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () => ref.refresh(productsProvider),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.forestGreen,
                  foregroundColor: Colors.white,
                ),
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: productsAsync.whenOrNull(
        data: (products) => FloatingActionButton.extended(
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(
                fullscreenDialog: true,
                builder: (_) => ClosingAuditDialog(
                  products: products,
                  storeId: activeStoreId,
                ),
              ),
            );
          },
          backgroundColor: context.primaryBrand,
          foregroundColor: context.isDarkMode ? Colors.black : Colors.white,
          icon: const Icon(Icons.assignment_turned_in_rounded),
          label: const Text(
            'Audit',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryChip({
    required String label,
    required ProductCategory? category,
  }) {
    final isSelected = _selectedCategory == category;

    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      showCheckmark: false,
      selectedColor: context.primaryBrand,
      backgroundColor: context.surfaceColor,
      labelStyle: TextStyle(
        color: isSelected ? (context.isDarkMode ? Colors.black : Colors.white) : context.textColor,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
        fontSize: 13,
      ),
      side: BorderSide(
        color: isSelected ? context.primaryBrand : context.dividerColor,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      onSelected: (_) {
        setState(() {
          _selectedCategory = category;
        });
      },
    );
  }
}
