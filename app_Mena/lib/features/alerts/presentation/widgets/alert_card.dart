import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../auth/domain/models/app_user.dart';
import '../../../auth/presentation/auth_providers.dart';
import '../../../catalog/presentation/catalog_providers.dart';
import '../../../dashboard/presentation/dashboard_providers.dart';
import '../../domain/models/spoilage_alert.dart';
import '../alerts_providers.dart';

class AlertCard extends ConsumerStatefulWidget {
  const AlertCard({
    required this.alert,
    super.key,
  });

  final SpoilageAlert alert;

  @override
  ConsumerState<AlertCard> createState() => _AlertCardState();
}

class _AlertCardState extends ConsumerState<AlertCard> {
  bool _isProcessing = false;

  Color _getUrgencyColor(int daysToExpiry) {
    if (daysToExpiry <= 0) {
      return context.criticalColor;
    } else if (daysToExpiry == 1) {
      return context.warningColor;
    } else {
      return context.warningColor;
    }
  }

  Future<void> _handleAcceptMarkdown() async {
    final user = ref.read(currentUserProvider);
    if (user?.role != UserRole.storeManager) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Access Restricted: Only Store Managers can apply markdowns.'),
          backgroundColor: AppColors.critical,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    setState(() => _isProcessing = true);
    final alert = widget.alert;

    try {
      final repository = ref.read(alertsRepositoryProvider);
      await repository.acceptMarkdown(alert.id);

      if (!mounted) return;

      ref.invalidate(alertsProvider);
      ref.invalidate(dashboardMetricsProvider);
      ref.invalidate(productsProvider);
      ref.invalidate(productBatchesProvider);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Markdown applied for ${alert.productName}'),
          backgroundColor: AppColors.safe,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to apply markdown: $e'),
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

  Future<void> _handleDismiss() async {
    setState(() => _isProcessing = true);
    final alert = widget.alert;

    try {
      final repository = ref.read(alertsRepositoryProvider);
      await repository.dismiss(alert.batchId ?? alert.id);

      if (!mounted) return;

      ref.invalidate(alertsProvider);
      ref.invalidate(dashboardMetricsProvider);

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Alert postponed for 6 hours'),
          backgroundColor: AppColors.textSecondary,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Could not dismiss alert. Try again.'),
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
    final canApplyMarkdown = user?.role == UserRole.storeManager;
    final alert = widget.alert;
    final urgencyColor = _getUrgencyColor(alert.daysToExpiry);
    final isOpen = alert.status == AlertStatus.open;
    final isAccepted = alert.status == AlertStatus.accepted;
    final isDismissed = alert.status == AlertStatus.dismissed;

    Widget cardContent = Card(
      elevation: 1.5,
      color: context.surfaceColor,
      clipBehavior: Clip.antiAlias,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: context.cardBorderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Top-left colored urgency indicator strip
          Container(
            height: 4,
            width: double.infinity,
            color: urgencyColor,
          ),

          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Row 1: product name (bold, 16px) + expiry chip
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        alert.productName,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: context.textColor,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: urgencyColor.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        alert.daysToExpiry <= 0
                            ? 'Expired'
                            : 'Expires in ${alert.daysToExpiry}d',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: urgencyColor,
                        ),
                      ),
                    ),
                  ],
                ),

                SizedBox(height: 12),

                // Row 2: two info columns side by side
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Current Stock',
                            style: TextStyle(
                              fontSize: 11,
                              color: context.textSecondaryColor,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Remaining: ${alert.remainingQty} units',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: context.textColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Model Forecast',
                            style: TextStyle(
                              fontSize: 11,
                              color: context.textSecondaryColor,
                            ),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Predicted Demand: ${alert.predictedDemand} units',
                            style: TextStyle(
                              fontSize: 13,
                              color: context.textSecondaryColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

                SizedBox(height: 12),

                // Row 3: suggestion text in a tinted container
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: context.isDarkMode
                        ? AppColors.darkWarning.withValues(alpha: 0.15)
                        : const Color(0xFFFFF8E1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: context.isDarkMode
                          ? AppColors.darkWarning.withValues(alpha: 0.4)
                          : const Color(0xFFFFE082),
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.local_offer_rounded,
                        color: context.warningColor,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Suggested: Apply ${(alert.suggestedDiscountPct * 100).toInt()}% discount to clear surplus',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: context.isDarkMode ? AppColors.darkWarning : const Color(0xFFBF360C),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                SizedBox(height: 12),

                // Row 4: Action buttons or Status Banner
                if (isOpen && canApplyMarkdown)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      OutlinedButton(
                        onPressed: _isProcessing ? null : _handleDismiss,
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.textSecondary,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          side: BorderSide(color: AppColors.divider),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        ),
                        child: Text('Dismiss'),
                      ),
                      if (canApplyMarkdown) ...[
                        SizedBox(width: 10),
                        ElevatedButton(
                          onPressed: _isProcessing ? null : _handleAcceptMarkdown,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.forestGreen,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                            elevation: 0,
                            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                          ),
                          child: _isProcessing
                              ? SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : Text(
                                  'Accept Markdown',
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                        ),
                      ],
                    ],
                  )
                else if (isAccepted)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: AppColors.safe.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.check_circle_rounded, color: AppColors.safe, size: 18),
                        const SizedBox(width: 6),
                        Text(
                          'Markdown Applied −${((alert.appliedDiscountPct ?? alert.suggestedDiscountPct) * 100).toInt()}%',
                          style: TextStyle(
                            color: AppColors.safe,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  )
                else if (isDismissed)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: context.isDarkMode ? AppColors.darkSurfaceVariant : Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.do_not_disturb_on_rounded,
                          color: context.textSecondaryColor,
                          size: 18,
                        ),
                        SizedBox(width: 6),
                        Text(
                          'Dismissed',
                          style: TextStyle(
                            color: context.textSecondaryColor,
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );

    if (isDismissed) {
      return Opacity(
        opacity: 0.6,
        child: cardContent,
      );
    }

    return cardContent;
  }
}
