import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/admin/presentation/screens/branches_screen.dart';
import '../../features/alerts/presentation/screens/alerts_screen.dart';
import '../../features/analytics/presentation/screens/analytics_screen.dart';
import '../../features/auth/domain/models/app_user.dart';
import '../../features/auth/presentation/auth_providers.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/broadcasts/presentation/screens/broadcasts_screen.dart';
import '../../features/catalog/presentation/screens/catalog_screen.dart';
import '../../features/dashboard/presentation/screens/dashboard_screen.dart';
import '../../features/reorder/presentation/screens/reorder_screen.dart';
import 'scaffold_with_nav_bar.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'root');

class RouterRefreshNotifier extends ChangeNotifier {
  RouterRefreshNotifier(Ref ref) {
    ref.listen(currentUserProvider, (previous, next) {
      notifyListeners();
    });
  }
}

/// Allowed paths per role to prevent unauthorized deep linking
final Map<UserRole, Set<String>> _allowedPaths = {
  UserRole.inventoryClerk: {'/catalog'},
  UserRole.inventoryAuditor: {'/catalog'},
  UserRole.storeManager: {'/dashboard', '/catalog', '/reorder', '/alerts', '/analytics', '/broadcasts'},
  UserRole.systemAdmin: {'/dashboard', '/catalog', '/stores', '/analytics', '/broadcasts'},
};

final appRouterProvider = Provider<GoRouter>((ref) {
  final refreshNotifier = RouterRefreshNotifier(ref);
  ref.onDispose(refreshNotifier.dispose);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/dashboard',
    refreshListenable: refreshNotifier,
    redirect: (context, state) {
      final user = ref.read(currentUserProvider);
      final isLoggingIn = state.matchedLocation == '/login';

      if (user == null && !isLoggingIn) {
        return '/login';
      }
      if (user != null && isLoggingIn) {
        final isClerkOrAuditor =
            user.role == UserRole.inventoryClerk || user.role == UserRole.inventoryAuditor;
        return isClerkOrAuditor ? '/catalog' : '/dashboard';
      }
      if (user != null) {
        final allowed = _allowedPaths[user.role] ?? {'/catalog'};
        if (!allowed.contains(state.matchedLocation)) {
          final isClerkOrAuditor =
              user.role == UserRole.inventoryClerk || user.role == UserRole.inventoryAuditor;
          return isClerkOrAuditor ? '/catalog' : '/dashboard';
        }
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/broadcasts',
        name: 'broadcasts',
        builder: (context, state) => const BroadcastsScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return ScaffoldWithNavBar(navigationShell: navigationShell);
        },
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/dashboard',
                name: 'dashboard',
                builder: (context, state) => const DashboardScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/catalog',
                name: 'catalog',
                builder: (context, state) => const CatalogScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/reorder',
                name: 'reorder',
                builder: (context, state) => const ReorderScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/alerts',
                name: 'alerts',
                builder: (context, state) => const AlertsScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/analytics',
                name: 'analytics',
                builder: (context, state) => const AnalyticsScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/stores',
                name: 'stores',
                builder: (context, state) => const BranchesScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
});
