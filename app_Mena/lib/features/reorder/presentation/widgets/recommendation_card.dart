import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../auth/domain/models/app_user.dart';
import '../../../auth/presentation/auth_providers.dart';
import '../../../catalog/domain/models/product.dart';
import '../../../dashboard/presentation/dashboard_providers.dart';
import '../../domain/models/recommendation.dart';
import '../reorder_providers.dart';

class RecommendationCard extends ConsumerStatefulWidget {
  const RecommendationCard({
    required this.recommendation,
    super.key,
  });

  final Recommendation recommendation;

  @override
  ConsumerState<RecommendationCard> createState() => _RecommendationCardState();
}

class _RecommendationCardState extends ConsumerState<RecommendationCard> {
  bool _isXaiExpanded = false;
  bool _isProcessing = false;

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

  Color _getStatusColor(RecommendationStatus status) {
    switch (status) {
      case RecommendationStatus.pending:
        return AppColors.warning;
      case RecommendationStatus.approved:
        return AppColors.safe;
      case RecommendationStatus.overridden:
        return AppColors.forestGreen;
    }
  }

  String _getStatusLabel(RecommendationStatus status) {
    switch (status) {
      case RecommendationStatus.pending:
        return 'Pending';
      case RecommendationStatus.approved:
        return 'Approved';
      case RecommendationStatus.overridden:
        return 'Overridden';
    }
  }

  Future<void> _handleApprove() async {
    final user = ref.read(currentUserProvider);
    if (user?.role != UserRole.storeManager) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Access Restricted: Only Store Managers can approve reorders.'),
          backgroundColor: AppColors.critical,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    setState(() => _isProcessing = true);
    final storeId = ref.read(activeStoreIdProvider);
    final rec = widget.recommendation;

    try {
      final repository = ref.read(reorderRepositoryProvider);
      final request = ApprovalRequest(
        storeId: storeId,
        items: [
          ApprovalItem(
            productId: rec.productId,
            finalQty: rec.recommendedQty,
            overrideReason: null,
          ),
        ],
      );

      final success = await repository.approve(request);

      if (!mounted) return;

      if (success) {
        ref.invalidate(recommendationsProvider);
        ref.invalidate(dashboardMetricsProvider);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Order approved for ${rec.productName}'),
            backgroundColor: AppColors.safe,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to approve: $e'),
          backgroundColor: AppColors.critical,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isProcessing = false);
      }
    }
  }

  void _showOverrideDialog() {
    final rec = widget.recommendation;
    int currentQty = rec.recommendedQty;
    String selectedReason = 'Manager Judgment';
    final reasons = [
      'Local Festival',
      'Weather Forecast',
      'Supplier Constraint',
      'Manager Judgment',
      'Other',
    ];

    final textController = TextEditingController(text: currentQty.toString());

    showDialog(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            void updateQty(int newQty) {
              if (newQty >= 0) {
                setDialogState(() {
                  currentQty = newQty;
                  textController.text = currentQty.toString();
                });
              }
            }

            return AlertDialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              title: Row(
                children: [
                  Icon(
                    Icons.edit_note_rounded,
                    color: context.primaryBrand,
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Override ${rec.productName}',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AI Recommendation: ${rec.recommendedQty} units',
                      style: TextStyle(
                        fontSize: 13,
                        color: context.textSecondaryColor,
                      ),
                    ),
                    SizedBox(height: 18),
                    Text(
                      'Adjusted Quantity',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    SizedBox(height: 8),
                    // Numeric Stepper Row
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                      decoration: BoxDecoration(
                        color: context.isDarkMode ? AppColors.darkSurfaceVariant : Colors.grey.shade50,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: context.dividerColor),
                      ),
                      child: Row(
                        children: [
                          IconButton(
                            icon: Icon(Icons.remove_circle_outline_rounded),
                            color: currentQty > 0 ? AppColors.forestGreen : Colors.grey,
                            onPressed: currentQty > 0 ? () => updateQty(currentQty - 1) : null,
                          ),
                          Expanded(
                            child: TextFormField(
                              controller: textController,
                              keyboardType: TextInputType.number,
                              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: context.textColor,
                              ),
                              decoration: const InputDecoration(
                                border: InputBorder.none,
                                enabledBorder: InputBorder.none,
                                focusedBorder: InputBorder.none,
                                isDense: true,
                                contentPadding: EdgeInsets.zero,
                              ),
                              onChanged: (val) {
                                final parsed = int.tryParse(val);
                                if (parsed != null && parsed >= 0) {
                                  setDialogState(() {
                                    currentQty = parsed;
                                  });
                                }
                              },
                            ),
                          ),
                          IconButton(
                            icon: Icon(Icons.add_circle_outline_rounded),
                            color: context.primaryBrand,
                            onPressed: () => updateQty(currentQty + 1),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(height: 18),
                    Text(
                      'Reason Code',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: context.dividerColor),
                        color: context.surfaceColor,
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: selectedReason,
                          isExpanded: true,
                          icon: const Icon(Icons.arrow_drop_down, color: AppColors.forestGreen),
                          items: reasons.map((reason) {
                            return DropdownMenuItem<String>(
                              value: reason,
                              child: Text(
                                reason,
                                style: const TextStyle(fontSize: 14),
                              ),
                            );
                          }).toList(),
                          onChanged: (newReason) {
                            if (newReason != null) {
                              setDialogState(() {
                                selectedReason = newReason;
                              });
                            }
                          },
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: const Text('Cancel', style: TextStyle(color: AppColors.textSecondary)),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.forestGreen,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () async {
                    Navigator.of(dialogContext).pop();
                    await _executeOverride(currentQty, selectedReason);
                  },
                  child: const Text('Confirm Override'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _executeOverride(int finalQty, String reason) async {
    setState(() => _isProcessing = true);
    final storeId = ref.read(activeStoreIdProvider);
    final rec = widget.recommendation;

    try {
      final repository = ref.read(reorderRepositoryProvider);
      final request = ApprovalRequest(
        storeId: storeId,
        items: [
          ApprovalItem(
            productId: rec.productId,
            finalQty: finalQty,
            overrideReason: reason,
          ),
        ],
      );

      final success = await repository.approve(request);

      if (!mounted) return;

      if (success) {
        // Track the reason code in presentation state
        ref.read(recommendationOverrideReasonsProvider.notifier).update((state) {
          return {...state, rec.productId: reason};
        });

        ref.invalidate(recommendationsProvider);
        ref.invalidate(dashboardMetricsProvider);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Overridden order set to $finalQty units ($reason)'),
            backgroundColor: AppColors.safe,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to override: $e'),
          backgroundColor: AppColors.critical,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isProcessing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider);
    final canApprove = user?.role == UserRole.storeManager;
    final rec = widget.recommendation;
    final isPending = rec.status == RecommendationStatus.pending;
    final isOverridden = rec.status == RecommendationStatus.overridden;
    final categoryColor = _getCategoryColor(rec.category, context.isDarkMode);
    final statusColor = _getStatusColor(rec.status);
    final statusLabel = _getStatusLabel(rec.status);

    final overrideReasonMap = ref.watch(recommendationOverrideReasonsProvider);
    final storedReason = overrideReasonMap[rec.productId];

    return Card(
      elevation: 1.5,
      color: context.surfaceColor,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: context.cardBorderColor),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. Header row: product name (bold) + category chip + status badge
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        rec.productName,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: context.textColor,
                        ),
                      ),
                      SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: categoryColor.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          _getCategoryName(rec.category),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: categoryColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: statusColor.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    statusLabel,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                ),
              ],
            ),

            SizedBox(height: 12),

            // 2. Info row: "Current: X" | "Safety: Y" | "Predicted: Z"
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: context.isDarkMode ? AppColors.darkSurfaceVariant : Colors.grey.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildInfoColumn('Current', rec.currentStock.toString()),
                  Container(height: 20, width: 1, color: context.dividerColor),
                  _buildInfoColumn('Safety', rec.safetyStock.toString()),
                  Container(height: 20, width: 1, color: context.dividerColor),
                  _buildInfoColumn('Predicted', rec.predictedDemand.toString()),
                ],
              ),
            ),

            SizedBox(height: 12),

            // 3. Recommended Qty (large and bold)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Order: ${isPending ? rec.recommendedQty : rec.approvedQty} units',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: context.primaryBrand,
                      ),
                    ),
                    if (isOverridden)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(
                          'Override Reason: ${storedReason ?? "Manager Judgment"}',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: context.textSecondaryColor,
                          ),
                        ),
                      ),
                  ],
                ),
                // Action Buttons
                if (isPending && canApprove)
                  Row(
                    children: [
                      TextButton(
                        onPressed: _isProcessing ? null : _showOverrideDialog,
                        style: TextButton.styleFrom(
                          foregroundColor: AppColors.textSecondary,
                          padding: const EdgeInsets.symmetric(horizontal: 10),
                        ),
                        child: const Text('Override'),
                      ),
                      const SizedBox(width: 4),
                      ElevatedButton(
                        onPressed: _isProcessing ? null : _handleApprove,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.forestGreen,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          elevation: 0,
                        ),
                        child: _isProcessing
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Text('Approve'),
                      ),
                    ],
                  )
                else if (!isPending)
                  Chip(
                    avatar: const Icon(Icons.check_circle_rounded, color: AppColors.safe, size: 18),
                    label: Text(
                      isOverridden ? 'Overridden ✓' : 'Approved ✓',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: isOverridden ? AppColors.forestGreen : AppColors.safe,
                        fontSize: 12,
                      ),
                    ),
                    backgroundColor: (isOverridden ? AppColors.forestGreen : AppColors.safe)
                        .withValues(alpha: 0.1),
                    side: BorderSide(
                      color: (isOverridden ? AppColors.forestGreen : AppColors.safe)
                          .withValues(alpha: 0.3),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                  ),
              ],
            ),

            const SizedBox(height: 8),

            // 5. XAI Card ("Why this amount?")
            InkWell(
              borderRadius: BorderRadius.circular(8),
              onTap: () {
                setState(() {
                  _isXaiExpanded = !_isXaiExpanded;
                });
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 6.0),
                child: Row(
                  children: [
                    Icon(
                      _isXaiExpanded ? Icons.psychology_rounded : Icons.psychology_outlined,
                      size: 18,
                      color: context.primaryBrand,
                    ),
                    SizedBox(width: 6),
                    Text(
                      'Why this amount?',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: context.primaryBrand,
                      ),
                    ),
                    const Spacer(),
                    Icon(
                      _isXaiExpanded
                          ? Icons.keyboard_arrow_up_rounded
                          : Icons.keyboard_arrow_down_rounded,
                      color: context.primaryBrand,
                      size: 20,
                    ),
                  ],
                ),
              ),
            ),

            if (_isXaiExpanded) ...[
              Container(
                margin: const EdgeInsets.only(top: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: (context.isDarkMode ? AppColors.darkSurfaceVariant : AppColors.surfaceVariant).withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: context.primaryBrand.withValues(alpha: 0.15),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      rec.xaiReason,
                      style: TextStyle(
                        fontSize: 13,
                        fontStyle: FontStyle.italic,
                        color: context.textColor,
                        height: 1.35,
                      ),
                    ),
                    if (rec.xaiDrivers.isNotEmpty) ...[
                      SizedBox(height: 12),
                      Text(
                        'Key Model Drivers',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: context.primaryBrand,
                          letterSpacing: 0.3,
                        ),
                      ),
                      const SizedBox(height: 8),
                      ...rec.xaiDrivers.map((driver) {
                        final progressValue = (driver.impactPct / 100.0).clamp(0.0, 1.0);
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4.0),
                          child: Row(
                            children: [
                              SizedBox(
                                width: 130,
                                child: Text(
                                  driver.label,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: context.textColor,
                                    fontWeight: FontWeight.w500,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              SizedBox(width: 8),
                              Expanded(
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(4),
                                  child: LinearProgressIndicator(
                                    value: progressValue,
                                    minHeight: 6,
                                    backgroundColor: Colors.grey.shade200,
                                    valueColor: const AlwaysStoppedAnimation<Color>(
                                      AppColors.forestGreen,
                                    ),
                                  ),
                                ),
                              ),
                              SizedBox(width: 10),
                              SizedBox(
                                width: 44,
                                child: Text(
                                  '${driver.impactPct.toStringAsFixed(1)}%',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: context.primaryBrand,
                                  ),
                                  textAlign: TextAlign.end,
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                    ],
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoColumn(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: context.textColor,
          ),
        ),
        SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(
            fontSize: 11,
            color: context.textSecondaryColor,
          ),
        ),
      ],
    );
  }
}
