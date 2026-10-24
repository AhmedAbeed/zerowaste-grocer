import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:zerowaste_grocer/features/alerts/presentation/alerts_providers.dart';
import 'package:zerowaste_grocer/features/analytics/presentation/analytics_providers.dart';
import 'package:zerowaste_grocer/features/auth/presentation/auth_providers.dart';
import 'package:zerowaste_grocer/features/catalog/presentation/catalog_providers.dart';
import 'package:zerowaste_grocer/features/dashboard/presentation/dashboard_providers.dart';
import 'package:zerowaste_grocer/features/notifications/presentation/notifications_providers.dart';
import 'package:zerowaste_grocer/features/reorder/presentation/reorder_providers.dart';

import 'repositories/mock_alerts_repository.dart';
import 'repositories/mock_analytics_repository.dart';
import 'repositories/mock_auth_repository.dart';
import 'repositories/mock_catalog_repository.dart';
import 'repositories/mock_dashboard_repository.dart';
import 'repositories/mock_notifications_repository.dart';
import 'repositories/mock_reorder_repository.dart';
import 'datasources/notifications_mock_datasource.dart';

List<Override> get mockRepositoryOverrides => [
  authRepositoryProvider.overrideWithValue(MockAuthRepository()),
  alertsRepositoryProvider.overrideWithValue(MockAlertsRepository()),
  catalogRepositoryProvider.overrideWithValue(MockCatalogRepository()),
  dashboardRepositoryProvider.overrideWithValue(MockDashboardRepository()),
  notificationsRepositoryProvider.overrideWithValue(
    MockNotificationsRepository(dataSource: NotificationsMockDataSource()),
  ),
  reorderRepositoryProvider.overrideWithValue(MockReorderRepository()),
  analyticsRepositoryProvider.overrideWithValue(MockAnalyticsRepository()),
];
