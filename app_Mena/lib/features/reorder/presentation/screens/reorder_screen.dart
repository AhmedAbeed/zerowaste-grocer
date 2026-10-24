import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../auth/domain/models/app_user.dart';
import '../../../auth/presentation/auth_providers.dart';
import '../../../catalog/domain/models/product.dart';
import '../../../dashboard/presentation/dashboard_providers.dart';
import '../../domain/models/recommendation.dart';
import '../reorder_providers.dart';
import '../widgets/recommendation_card.dart';

class ReorderScreen extends ConsumerWidget {
  const ReorderScreen({super.key});

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

  String _getCategoryName(ProductCategory category) {
    switch (category) {
      case ProductCategory.produce:
        return 'Produce';
      case ProductCategory.dairy:
        return 'Dairy';
      case ProductCategory.bakery:
        return 'Bakery';
      case ProductCategory.butchery:
        return 'Butchery';
    }
  }

  Future<void> _handleApproveAll(
    BuildContext context,
    WidgetRef ref,
    int storeId,
    List<Recommendation> pendingRecommendations,
  ) async {
    try {
      final repository = ref.read(reorderRepositoryProvider);
      final request = ApprovalRequest(
        storeId: storeId,
        items: pendingRecommendations.map((r) {
          return ApprovalItem(
            productId: r.productId,
            finalQty: r.recommendedQty,
            overrideReason: null,
          );
        }).toList(),
      );

      final success = await repository.approve(request);

      if (context.mounted && success) {
        ref.invalidate(recommendationsProvider);
        ref.invalidate(dashboardMetricsProvider);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Approved all ${pendingRecommendations.length} pending recommendations',
            ),
            backgroundColor: AppColors.safe,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to approve all: $e'),
            backgroundColor: AppColors.critical,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    if (user != null && user.role == UserRole.inventoryAuditor) {
      return Scaffold(
        
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.shield_outlined, size: 64, color: context.textSecondaryColor),
                const SizedBox(height: 16),
                Text(
                  'Access Restricted',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: context.primaryBrand),
                ),
                const SizedBox(height: 8),
                Text(
                  'Replenishment reorder recommendations and purchase approvals are restricted to Store Managers and System Administrators.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: context.textSecondaryColor, fontSize: 14),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final recommendationsAsync = ref.watch(recommendationsProvider);
    final activeStoreId = ref.watch(activeStoreIdProvider);

    return Scaffold(
      
      body: recommendationsAsync.when(
        data: (recommendations) {
          if (recommendations.isEmpty) {
            return const Center(
              child: Text(
                'No replenishment recommendations found.',
                style: TextStyle(color: AppColors.textSecondary),
              ),
            );
          }

          final pending = recommendations
              .where((r) => r.status == RecommendationStatus.pending)
              .toList();

          // Group recommendations by category
          final Map<ProductCategory, List<Recommendation>> grouped = {};
          for (final rec in recommendations) {
            grouped.putIfAbsent(rec.category, () => []).add(rec);
          }

          final orderedCategories = [
            ProductCategory.produce,
            ProductCategory.dairy,
            ProductCategory.bakery,
            ProductCategory.butchery,
          ];

          return RefreshIndicator(
            color: context.primaryBrand,
            onRefresh: () async {
              return ref.refresh(recommendationsProvider.future);
            },
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 900),
                child: ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.only(top: 14, bottom: 28),
                  children: [
                // Header / Action Bar with "Approve All"
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'AI Replenishment',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: context.primaryBrand,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            '${pending.length} pending approval · ${recommendations.length} total',
                            style: TextStyle(
                              fontSize: 12,
                              color: context.textSecondaryColor,
                            ),
                          ),
                        ],
                      ),
                      if (pending.isNotEmpty && user?.role == UserRole.storeManager)
                        ElevatedButton.icon(
                          onPressed: () => _handleApproveAll(
                            context,
                            ref,
                            activeStoreId,
                            pending,
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.forestGreen,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 10,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            elevation: 0,
                          ),
                          icon: Icon(Icons.done_all_rounded, size: 18),
                          label: Text(
                            'Approve All (${pending.length})',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),

                SizedBox(height: 6),

                // Grouped Categories
                for (final category in orderedCategories)
                  if (grouped.containsKey(category) && grouped[category]!.isNotEmpty) ...[
                    Padding(
                      padding: const EdgeInsets.fromLTRB(18, 14, 18, 6),
                      child: Row(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: _getCategoryColor(category, context.isDarkMode),
                              shape: BoxShape.circle,
                            ),
                          ),
                          SizedBox(width: 8),
                          Text(
                            _getCategoryName(category).toUpperCase(),
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 0.8,
                              color: _getCategoryColor(category, context.isDarkMode),
                            ),
                          ),
                          SizedBox(width: 6),
                          Text(
                            '(${grouped[category]!.length})',
                            style: TextStyle(
                              fontSize: 12,
                              color: context.textSecondaryColor,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Divider(
                              color: Colors.grey.shade300,
                              thickness: 1,
                            ),
                          ),
                        ],
                      ),
                    ),
                    for (final rec in grouped[category]!)
                      RecommendationCard(recommendation: rec),
                  ],
                ],
              ),
            ),
          ),
        );
      },
        loading: () => Center(
          child: CircularProgressIndicator(color: AppColors.forestGreen),
        ),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.error_outline_rounded,
                  size: 48,
                  color: context.criticalColor,
                ),
                SizedBox(height: 12),
                Text(
                  'Failed to load replenishment recommendations',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 6),
                Text(
                  error.toString(),
                  style: TextStyle(color: context.textSecondaryColor, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 18),
                ElevatedButton.icon(
                  onPressed: () => ref.refresh(recommendationsProvider),
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
      ),
    );
  }
}
