import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../core/theme/app_colors.dart';
import '../../domain/models/product.dart';
import '../catalog_providers.dart';

class ProductCard extends StatelessWidget {
  const ProductCard({
    required this.product,
    super.key,
  });

  final Product product;

  Color _getCategoryColor(ProductCategory category, bool isDark) {
    if (isDark) {
      switch (category) {
        case ProductCategory.produce: return AppColors.catProduce;
        case ProductCategory.dairy: return AppColors.catDairy;
        case ProductCategory.bakery: return AppColors.catBakery;
        case ProductCategory.butchery: return AppColors.catMeat;
      }
    }
    switch (category) {
      case ProductCategory.produce: return const Color(0xFF2E7D32);
      case ProductCategory.dairy: return const Color(0xFF0288D1);
      case ProductCategory.bakery: return const Color(0xFFE65100);
      case ProductCategory.butchery: return const Color(0xFFC2185B);
    }
  }

  String _getCategoryInitial(ProductCategory category) {
    switch (category) {
      case ProductCategory.produce:
        return 'P';
      case ProductCategory.dairy:
        return 'D';
      case ProductCategory.bakery:
        return 'B';
      case ProductCategory.butchery:
        return 'B';
    }
  }

  Color _getStockColor(int currentStock, int safetyStock, BuildContext context) {
    if (currentStock <= (safetyStock * 0.5)) {
      return context.criticalColor;
    } else if (currentStock <= safetyStock) {
      return context.warningColor;
    } else {
      return context.safeColor;
    }
  }

  void _showBatchesBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: context.surfaceColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (bottomSheetContext) {
        return DraggableScrollableSheet(
          initialChildSize: 0.55,
          minChildSize: 0.35,
          maxChildSize: 0.85,
          expand: false,
          builder: (context, scrollController) {
            return Consumer(
              builder: (context, ref, child) {
                final batchesAsync = ref.watch(productBatchesProvider(product.id));
                final dateFormat = DateFormat('MMM dd');

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Center(
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 12),
                        height: 4,
                        width: 40,
                        decoration: BoxDecoration(
                          color: Colors.grey.shade300,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          CircleAvatar(
                            radius: 20,
                            backgroundColor: _getCategoryColor(product.category, context.isDarkMode),
                            child: Text(
                              _getCategoryInitial(product.category),
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                          ),
                          SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  product.name,
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: context.textColor,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'SKU: ${product.sku} · Total Stock: ${product.currentStock}',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: context.textSecondaryColor,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close_rounded),
                            onPressed: () => Navigator.of(bottomSheetContext).pop(),
                          ),
                        ],
                      ),
                    ),
                    const Divider(height: 1),
                    Expanded(
                      child: batchesAsync.when(
                        data: (batches) {
                          if (batches.isEmpty) {
                            return const Center(
                              child: Text(
                                'No active batches found for this product.',
                                style: TextStyle(color: AppColors.textSecondary),
                              ),
                            );
                          }

                          return ListView.separated(
                            controller: scrollController,
                            padding: const EdgeInsets.all(16),
                            itemCount: batches.length,
                            separatorBuilder: (context, index) => const SizedBox(height: 10),
                            itemBuilder: (context, index) {
                              final batch = batches[index];
                              final daysUntilExpiry = batch.daysToExpiry ??
                                  batch.expirationDate.difference(DateTime.now()).inDays;
                              final isExpiringSoon = daysUntilExpiry <= 2;

                              return Card(
                                elevation: 0.5,
                                color: isExpiringSoon
                                    ? const Color(0xFFFFF3E0)
                                    : Colors.grey.shade50,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(10),
                                  side: BorderSide(
                                    color: isExpiringSoon
                                        ? AppColors.warning.withValues(alpha: 0.5)
                                        : AppColors.cardBorder,
                                  ),
                                ),
                                child: Padding(
                                  padding: const EdgeInsets.all(14.0),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            'Batch #${batch.id}',
                                            style: TextStyle(
                                              fontWeight: FontWeight.bold,
                                              fontSize: 14,
                                            ),
                                          ),
                                          Container(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 8,
                                              vertical: 3,
                                            ),
                                            decoration: BoxDecoration(
                                              color: isExpiringSoon
                                                  ? AppColors.critical.withValues(alpha: 0.12)
                                                  : AppColors.safe.withValues(alpha: 0.12),
                                              borderRadius: BorderRadius.circular(6),
                                            ),
                                            child: Text(
                                              daysUntilExpiry <= 0
                                                  ? 'Expired'
                                                  : 'Expires in ${daysUntilExpiry}d',
                                              style: TextStyle(
                                                fontSize: 12,
                                                fontWeight: FontWeight.w600,
                                                color: isExpiringSoon
                                                    ? AppColors.critical
                                                    : AppColors.safe,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                      SizedBox(height: 10),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            'Received: ${dateFormat.format(batch.receivedDate)}',
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: context.textSecondaryColor,
                                            ),
                                          ),
                                          Text(
                                            'Expires: ${dateFormat.format(batch.expirationDate)}',
                                            style: TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.w600,
                                              color: context.textColor,
                                            ),
                                          ),
                                        ],
                                      ),
                                      SizedBox(height: 6),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            'Remaining: ${batch.remainingQty} units',
                                            style: TextStyle(
                                              fontSize: 13,
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                          if (batch.discountPct > 0)
                                            Container(
                                              padding: const EdgeInsets.symmetric(
                                                horizontal: 6,
                                                vertical: 2,
                                              ),
                                              decoration: BoxDecoration(
                                                color: context.criticalColor,
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(
                                                '-${(batch.discountPct * 100).toInt()}% off',
                                                style: TextStyle(
                                                  color: Colors.white,
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.bold,
                                                ),
                                              ),
                                            )
                                          else
                                            Text(
                                              'No discount',
                                              style: TextStyle(
                                                fontSize: 12,
                                                color: context.textSecondaryColor,
                                              ),
                                            ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          );
                        },
                        loading: () => const Center(
                          child: CircularProgressIndicator(color: AppColors.forestGreen),
                        ),
                        error: (error, _) => Center(
                          child: Text(
                            'Failed to load batches: $error',
                            style: const TextStyle(color: AppColors.critical),
                          ),
                        ),
                      ),
                    ),
                  ],
                );
              },
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final stockColor = _getStockColor(product.currentStock, product.safetyStock, context);
    final categoryColor = _getCategoryColor(product.category, context.isDarkMode);

    return Card(
      elevation: 1,
      color: context.surfaceColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: context.cardBorderColor),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _showBatchesBottomSheet(context),
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: categoryColor,
                child: Text(
                  _getCategoryInitial(product.category),
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ),
              SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      product.name,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: context.textColor,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    SizedBox(height: 3),
                    Text(
                      product.sku,
                      style: TextStyle(
                        fontSize: 12,
                        color: context.textSecondaryColor,
                        letterSpacing: 0.2,
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    'Stock: ${product.currentStock}',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: stockColor,
                    ),
                  ),
                  SizedBox(height: 3),
                  Text(
                    'Shelf: ${product.shelfLifeDays}d',
                    style: TextStyle(
                      fontSize: 12,
                      color: context.textSecondaryColor,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
