import 'dart:math';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../auth/domain/models/app_user.dart';
import '../../../auth/presentation/auth_providers.dart';
import '../../../catalog/domain/models/product.dart';
import '../../domain/models/waste_metrics.dart';
import '../analytics_providers.dart';

class AnalyticsScreen extends ConsumerWidget {
  const AnalyticsScreen({super.key});

  Color _getCategoryColor(ProductCategory category, bool isDark) {
    if (isDark) {
      switch (category) {
        case ProductCategory.produce:
          return AppColors.catProduce;
        case ProductCategory.dairy:
          return AppColors.catDairy;
        case ProductCategory.bakery:
          return AppColors.catBakery;
        case ProductCategory.butchery:
          return AppColors.catMeat;
      }
    } else {
      switch (category) {
        case ProductCategory.produce:
          return const Color(0xFF2E7D32);
        case ProductCategory.dairy:
          return const Color(0xFF0288D1);
        case ProductCategory.bakery:
          return const Color(0xFFE65100);
        case ProductCategory.butchery:
          return const Color(0xFFC2185B);
      }
    }
  }

  String _getCategoryNameByIndex(int index) {
    switch (index) {
      case 0:
        return 'Produce';
      case 1:
        return 'Dairy';
      case 2:
        return 'Bakery';
      case 3:
        return 'Butchery';
      default:
        return '';
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final isDark = context.isDarkMode;

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
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: context.textColor,
                      ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Store Performance Analytics is reserved for Store Managers and System Administrators.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: context.textSecondaryColor),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final metricsAsync = ref.watch(analyticsMetricsProvider);
    final salesSeriesAsync = ref.watch(analyticsSalesSeriesProvider);
    final categoryWasteAsync = ref.watch(analyticsCategoryWasteProvider);

    final isLoading = metricsAsync.isLoading || salesSeriesAsync.isLoading || categoryWasteAsync.isLoading;
    final hasError = metricsAsync.hasError || salesSeriesAsync.hasError || categoryWasteAsync.hasError;

    if (isLoading && !metricsAsync.hasValue) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (hasError && !metricsAsync.hasValue) {
      final error = metricsAsync.error ?? salesSeriesAsync.error ?? categoryWasteAsync.error;
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.error_outline_rounded,
                  size: 48,
                  color: context.criticalColor,
                ),
                const SizedBox(height: 12),
                Text(
                  'Failed to load analytics data',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: context.textColor,
                      ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 6),
                Text(
                  error.toString(),
                  style: TextStyle(color: context.textSecondaryColor, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 18),
                ElevatedButton.icon(
                  onPressed: () {
                    ref.invalidate(analyticsMetricsProvider);
                    ref.invalidate(analyticsSalesSeriesProvider);
                    ref.invalidate(analyticsCategoryWasteProvider);
                  },
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
      );
    }

    final salesPoints = salesSeriesAsync.value ?? [];
    final categoryWaste = categoryWasteAsync.value ?? [];

    return Scaffold(
      body: RefreshIndicator(
        color: context.primaryBrand,
        onRefresh: () async {
          await Future.wait([
            ref.refresh(analyticsMetricsProvider.future),
            ref.refresh(analyticsSalesSeriesProvider.future),
            ref.refresh(analyticsCategoryWasteProvider.future),
          ]);
        },
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 900),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 18.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Header
                  Text(
                    'Performance Analytics',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: context.primaryBrand,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'AI demand accuracy & waste reduction trends',
                    style: TextStyle(
                      fontSize: 12,
                      color: context.textSecondaryColor,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // CHART 1: Actual vs Predicted Sales
                  _buildActualVsPredictedCard(context, salesPoints, isDark),
                  const SizedBox(height: 16),

                  // CHART 2: Cumulative Waste Reduction
                  _buildCumulativeWasteCard(context, salesPoints, isDark),
                  const SizedBox(height: 16),

                  // CHART 3: Waste by Category
                  _buildWasteByCategoryCard(context, categoryWaste, isDark),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // --- CHART 1: Actual vs Predicted Sales ---
  Widget _buildActualVsPredictedCard(BuildContext context, List<SalesPoint> salesPoints, bool isDark) {
    if (salesPoints.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Center(
            child: Text(
              'No sales history available.',
              style: TextStyle(color: context.textSecondaryColor),
            ),
          ),
        ),
      );
    }

    final dayFormat = DateFormat('MM/dd');
    final actualSpots = <FlSpot>[];
    final predictedSpots = <FlSpot>[];

    double minY = double.infinity;
    double maxY = double.negativeInfinity;

    for (var i = 0; i < salesPoints.length; i++) {
      final p = salesPoints[i];
      actualSpots.add(FlSpot(i.toDouble(), p.actual));
      predictedSpots.add(FlSpot(i.toDouble(), p.predicted));

      minY = min(minY, min(p.actual, p.predicted));
      maxY = max(maxY, max(p.actual, p.predicted));
    }

    final adjustedMinY = (minY * 0.9).floorToDouble();
    final adjustedMaxY = (maxY * 1.1).ceilToDouble();

    final actualLineColor = isDark ? AppColors.catProduce : AppColors.forestGreen;
    final predLineColor = isDark ? AppColors.catBakery : AppColors.warning;

    return Card(
      elevation: 1.5,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: context.cardBorderColor),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Actual vs Predicted Sales',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: context.textColor,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              'Last 30 days',
              style: TextStyle(
                fontSize: 12,
                color: context.textSecondaryColor,
              ),
            ),
            const SizedBox(height: 18),
            SizedBox(
              height: 220,
              child: LineChart(
                LineChartData(
                  minY: adjustedMinY,
                  maxY: adjustedMaxY,
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: context.dividerColor,
                      strokeWidth: 0.8,
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 22,
                        interval: 1,
                        getTitlesWidget: (value, meta) {
                          final index = value.toInt();
                          if (index >= 0 && index < salesPoints.length && index % 5 == 0) {
                            return Text(
                              dayFormat.format(salesPoints[index].date),
                              style: TextStyle(
                                fontSize: 10,
                                color: context.textSecondaryColor,
                              ),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            '${(value / 1000).toStringAsFixed(1)}k',
                            style: TextStyle(
                              fontSize: 10,
                              color: context.textSecondaryColor,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  lineTouchData: LineTouchData(
                    enabled: true,
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipColor: (spot) => isDark ? const Color(0xFF243B28) : AppColors.forestGreen,
                      getTooltipItems: (touchedSpots) {
                        return touchedSpots.map((spot) {
                          final isActual = spot.barIndex == 0;
                          return LineTooltipItem(
                            '${isActual ? "Actual" : "Pred"}: \${spot.y.toInt()}',
                            const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          );
                        }).toList();
                      },
                    ),
                  ),
                  lineBarsData: [
                    // Line 1: Actual
                    LineChartBarData(
                      spots: actualSpots,
                      color: actualLineColor,
                      isCurved: true,
                      barWidth: 2.5,
                      dotData: const FlDotData(show: false),
                    ),
                    // Line 2: Predicted
                    LineChartBarData(
                      spots: predictedSpots,
                      color: predLineColor,
                      isCurved: true,
                      dashArray: const [6, 4],
                      barWidth: 2.0,
                      dotData: const FlDotData(show: false),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            // Legend
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 12,
                  height: 3,
                  color: actualLineColor,
                ),
                const SizedBox(width: 4),
                Text('Actual', style: TextStyle(fontSize: 11, color: context.textColor)),
                const SizedBox(width: 18),
                Container(
                  width: 12,
                  height: 3,
                  color: predLineColor,
                ),
                const SizedBox(width: 4),
                Text('Predicted', style: TextStyle(fontSize: 11, color: context.textColor)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // --- CHART 2: Cumulative Waste Reduction ---
  Widget _buildCumulativeWasteCard(BuildContext context, List<SalesPoint> salesPoints, bool isDark) {
    if (salesPoints.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Center(
            child: Text(
              'No waste data available.',
              style: TextStyle(color: context.textSecondaryColor),
            ),
          ),
        ),
      );
    }

    final dayFormat = DateFormat('MM/dd');
    final cumulativeSpots = <FlSpot>[];
    double runningTotal = 0;

    for (var i = 0; i < salesPoints.length; i++) {
      final p = salesPoints[i];
      final avoidedUnits = max(0.0, (p.predicted - p.actual) / 10.0);
      runningTotal += avoidedUnits;
      cumulativeSpots.add(FlSpot(i.toDouble(), runningTotal));
    }

    final maxY = (runningTotal * 1.15).ceilToDouble();
    final seriesColor = isDark ? AppColors.darkSafe : AppColors.safe;

    return Card(
      elevation: 1.5,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: context.cardBorderColor),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Cumulative Waste Reduction',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: context.textColor,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              'Avoided waste units over 30 days',
              style: TextStyle(
                fontSize: 12,
                color: context.textSecondaryColor,
              ),
            ),
            const SizedBox(height: 18),
            SizedBox(
              height: 200,
              child: LineChart(
                LineChartData(
                  minY: 0,
                  maxY: max(10, maxY),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: context.dividerColor,
                      strokeWidth: 0.8,
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 22,
                        interval: 1,
                        getTitlesWidget: (value, meta) {
                          final index = value.toInt();
                          if (index >= 0 && index < salesPoints.length && index % 5 == 0) {
                            return Text(
                              dayFormat.format(salesPoints[index].date),
                              style: TextStyle(
                                fontSize: 10,
                                color: context.textSecondaryColor,
                              ),
                            );
                          }
                          return const SizedBox.shrink();
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toInt().toString(),
                            style: TextStyle(
                              fontSize: 10,
                              color: context.textSecondaryColor,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  lineTouchData: LineTouchData(
                    enabled: true,
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipColor: (spot) => isDark ? const Color(0xFF243B28) : AppColors.forestGreen,
                      getTooltipItems: (touchedSpots) {
                        return touchedSpots.map((spot) {
                          return LineTooltipItem(
                            '${spot.y.toInt()} units',
                            const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          );
                        }).toList();
                      },
                    ),
                  ),
                  lineBarsData: [
                    LineChartBarData(
                      spots: cumulativeSpots,
                      color: seriesColor,
                      isCurved: true,
                      barWidth: 2.5,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        color: seriesColor.withValues(alpha: isDark ? 0.25 : 0.15),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            // Legend
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 12,
                  height: 3,
                  color: seriesColor,
                ),
                const SizedBox(width: 4),
                Text('Waste Avoided (units)', style: TextStyle(fontSize: 11, color: context.textColor)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // --- CHART 3: Waste by Category ---
  Widget _buildWasteByCategoryCard(BuildContext context, List<CategoryWaste> categoryWaste, bool isDark) {
    if (categoryWaste.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Center(
            child: Text(
              'No category waste metrics found.',
              style: TextStyle(color: context.textSecondaryColor),
            ),
          ),
        ),
      );
    }

    final groups = <BarChartGroupData>[];
    double maxVal = 0;

    final categories = [
      ProductCategory.produce,
      ProductCategory.dairy,
      ProductCategory.bakery,
      ProductCategory.butchery,
    ];

    for (var i = 0; i < categories.length; i++) {
      final cat = categories[i];
      final item = categoryWaste.firstWhere(
        (c) => c.category == cat,
        orElse: () => CategoryWaste(category: cat, units: 0),
      );
      final units = item.units.toDouble();
      maxVal = max(maxVal, units);
      final catColor = _getCategoryColor(cat, isDark);

      groups.add(
        BarChartGroupData(
          x: i,
          barRods: [
            BarChartRodData(
              toY: units,
              color: catColor,
              width: 22,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
            ),
          ],
        ),
      );
    }

    final maxY = (maxVal * 1.2).ceilToDouble();

    return Card(
      elevation: 1.5,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: context.cardBorderColor),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Waste by Category',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: context.textColor,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              'Recorded discarded units per department',
              style: TextStyle(
                fontSize: 12,
                color: context.textSecondaryColor,
              ),
            ),
            const SizedBox(height: 18),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  maxY: max(20, maxY),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    getDrawingHorizontalLine: (value) => FlLine(
                      color: context.dividerColor,
                      strokeWidth: 0.8,
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 36,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toInt().toString(),
                            style: TextStyle(
                              fontSize: 10,
                              color: context.textSecondaryColor,
                            ),
                          );
                        },
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 26,
                        getTitlesWidget: (value, meta) {
                          final name = _getCategoryNameByIndex(value.toInt());
                          return Padding(
                            padding: const EdgeInsets.only(top: 6.0),
                            child: Text(
                              name,
                              style: TextStyle(
                                fontSize: 11,
                                color: context.textSecondaryColor,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  barTouchData: BarTouchData(
                    enabled: true,
                    touchTooltipData: BarTouchTooltipData(
                      getTooltipColor: (group) => isDark ? const Color(0xFF243B28) : AppColors.forestGreen,
                      getTooltipItem: (group, groupIndex, rod, rodIndex) {
                        final name = _getCategoryNameByIndex(group.x);
                        return BarTooltipItem(
                          '$name\n${rod.toY.toInt()} units',
                          const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        );
                      },
                    ),
                  ),
                  barGroups: groups,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
