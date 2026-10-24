import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../dashboard_providers.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final metricsAsync = ref.watch(dashboardMetricsProvider);

    return Scaffold(
      
      body: metricsAsync.when(
        data: (metrics) {
          final screenWidth = MediaQuery.of(context).size.width;
          final isWide = screenWidth > 600;

          return RefreshIndicator(
            color: context.primaryBrand,
            onRefresh: () async {
              return ref.refresh(dashboardMetricsProvider.future);
            },
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 900),
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 20.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Store Dashboard',
                                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                      fontWeight: FontWeight.bold,
                                      color: context.primaryBrand,
                                    ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Real-time spoilage & sustainability tracker',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: context.textSecondaryColor,
                                    ),
                              ),
                            ],
                          ),
                          IconButton(
                            icon: Icon(Icons.refresh_rounded, color: context.primaryBrand),
                            tooltip: 'Refresh metrics',
                            onPressed: () => ref.refresh(dashboardMetricsProvider),
                          ),
                        ],
                      ),
                      SizedBox(height: 20),
                      GridView.count(
                        crossAxisCount: isWide ? 4 : 2,
                        crossAxisSpacing: 14,
                        mainAxisSpacing: 14,
                        childAspectRatio: isWide ? 1.25 : 1.15,
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        children: [
                    // Card A: Units at Risk
                    _buildKpiCard(
                      context: context,
                      label: 'Units at Risk',
                      value: metrics.unitsAtRisk.toString(),
                      icon: Icons.warning_amber_rounded,
                      iconColor: metrics.unitsAtRisk > 0
                          ? AppColors.critical
                          : AppColors.safe,
                    ),
                    // Card B: Projected Exposure
                    _buildKpiCard(
                      context: context,
                      label: 'Projected Exposure',
                      value: '\$${metrics.projectedExposure.toStringAsFixed(2)}',
                      icon: Icons.attach_money_rounded,
                      iconColor: AppColors.warning,
                    ),
                    // Card C: Pending Orders
                    _buildKpiCard(
                      context: context,
                      label: 'Pending Orders',
                      value: metrics.pendingOrders.toString(),
                      icon: Icons.pending_actions_rounded,
                      iconColor: AppColors.forestGreen,
                    ),
                    // Card D: Kg Saved / CO2e
                    _buildKpiCard(
                      context: context,
                      label: 'Kg Saved / CO₂e',
                      value: '${metrics.kgSaved} kg · ${metrics.co2Saved} CO₂e',
                      icon: Icons.eco_rounded,
                      iconColor: AppColors.safe,
                      isValueCompact: true,
                    ),
                  ],
                ),
                SizedBox(height: 24),
                // Sustainability Highlights Card
                Card(
                  elevation: 1.5,
                  
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: context.cardBorderColor),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: context.isDarkMode ? AppColors.darkSurfaceVariant : AppColors.surfaceVariant,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.energy_savings_leaf_outlined,
                            color: context.primaryBrand,
                            size: 28,
                          ),
                        ),
                        SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Eco-Impact Active',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: context.primaryBrand,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                '${metrics.kgSaved} kg of food diverted from landfills. Keep monitoring markdown alerts and approving daily replenishment.',
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
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  },
        loading: () => Center(
          child: CircularProgressIndicator(
            color: context.primaryBrand,
          ),
        ),
        error: (error, stack) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.error_outline_rounded,
                  size: 48,
                  color: AppColors.critical,
                ),
                SizedBox(height: 12),
                Text(
                  'Failed to load dashboard metrics',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 8),
                Text(
                  error.toString(),
                  style: TextStyle(color: context.textSecondaryColor, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 20),
                ElevatedButton.icon(
                  onPressed: () => ref.refresh(dashboardMetricsProvider),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.forestGreen,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  icon: const Icon(Icons.refresh_rounded, size: 18),
                  label: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildKpiCard({
    required BuildContext context,
    required String label,
    required String value,
    required IconData icon,
    required Color iconColor,
    bool isValueCompact = false,
  }) {
    return Card(
      elevation: 1.5,
      
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: context.cardBorderColor),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: iconColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    icon,
                    size: 24,
                    color: iconColor,
                  ),
                ),
              ],
            ),
            const Spacer(),
            Text(
              value,
              style: TextStyle(
                fontSize: isValueCompact ? 14 : 20,
                fontWeight: FontWeight.bold,
                color: context.textColor,
                letterSpacing: -0.3,
              ),
              maxLines: isValueCompact ? 2 : 1,
              overflow: TextOverflow.ellipsis,
            ),
            SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: context.textSecondaryColor,
                fontWeight: FontWeight.w500,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }
}
