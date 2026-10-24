import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../auth/domain/models/app_user.dart';
import '../../../auth/presentation/auth_providers.dart';
import '../../../notifications/presentation/notifications_providers.dart';
import '../../domain/models/spoilage_alert.dart';
import '../alerts_providers.dart';
import '../widgets/alert_card.dart';

class AlertsScreen extends ConsumerWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alertsAsync = ref.watch(alertsProvider);

    return Scaffold(
      
      body: alertsAsync.when(
        data: (alerts) {
          if (alerts.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.notifications_off_outlined,
                      size: 48,
                      color: context.textSecondaryColor,
                    ),
                    const SizedBox(height: 14),
                    Text(
                      'No spoilage alerts',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: context.textColor,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'All batches are within safe expiration windows',
                      style: TextStyle(
                        fontSize: 13,
                        color: context.textSecondaryColor,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            );
          }

          final openAlerts = alerts.where((a) => a.status == AlertStatus.open).toList();
          final activeAlertsCount = openAlerts.length;
          final unitsAtRisk = openAlerts.fold<int>(0, (sum, a) => sum + a.remainingQty);
          final acceptedCount = alerts.where((a) => a.status == AlertStatus.accepted).length;
          final headerText = acceptedCount > 0
              ? '$activeAlertsCount active alerts · $unitsAtRisk units at risk · $acceptedCount applied'
              : '$activeAlertsCount active alerts · $unitsAtRisk units at risk';

          return RefreshIndicator(
            color: context.primaryBrand,
            onRefresh: () async {
              final user = ref.read(currentUserProvider);
              if (user?.role == UserRole.storeManager) {
                await markAllReadForStore(ref);
              }
              return ref.refresh(alertsProvider.future);
            },
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 900),
                child: ListView.builder(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.only(top: 14, bottom: 28),
                  itemCount: alerts.length + 1,
                  itemBuilder: (context, index) {
                if (index == 0) {
                  return Padding(
                    padding: const EdgeInsets.fromLTRB(18, 4, 18, 10),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(6),
                              decoration: BoxDecoration(
                                color: (activeAlertsCount > 0 ? AppColors.warning : AppColors.safe)
                                    .withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Icon(
                                Icons.notifications_active_rounded,
                                size: 18,
                                color: activeAlertsCount > 0 ? AppColors.warning : AppColors.safe,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              headerText,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                                color: context.textColor,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  );
                }

                final alert = alerts[index - 1];
                return AlertCard(alert: alert);
              },
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
                  'Failed to load spoilage alerts',
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
                  onPressed: () => ref.refresh(alertsProvider),
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
