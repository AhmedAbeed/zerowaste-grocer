import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/alerts/presentation/alerts_providers.dart';
import '../../features/auth/domain/models/app_user.dart';
import '../../features/auth/presentation/auth_providers.dart';
import '../../features/dashboard/presentation/dashboard_providers.dart';
import '../../features/notifications/presentation/notifications_providers.dart';
import '../network/dio_client.dart';
import '../offline/offline_queue_service.dart';
import '../theme/app_colors.dart';
import '../theme/theme_provider.dart';

class ScaffoldWithNavBar extends ConsumerStatefulWidget {
  const ScaffoldWithNavBar({
    required this.navigationShell,
    super.key,
  });

  final StatefulNavigationShell navigationShell;

  @override
  ConsumerState<ScaffoldWithNavBar> createState() => _ScaffoldWithNavBarState();
}

class _ScaffoldWithNavBarState extends ConsumerState<ScaffoldWithNavBar> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      try {
        final dio = ref.read(dioProvider);
        final synced = await OfflineQueueService.syncOfflineQueue(dio);
        if (synced > 0 && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Offline changes synced to server'),
              backgroundColor: AppColors.safe,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      } catch (_) {
        // Ignored if network remains unreachable on startup
      }
    });
  }

  @override
  void didUpdateWidget(ScaffoldWithNavBar oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.navigationShell.currentIndex != oldWidget.navigationShell.currentIndex) {
      if (widget.navigationShell.currentIndex == 3) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          final user = ref.read(currentUserProvider);
          if (user?.role == UserRole.storeManager) {
            markAllReadForStore(ref);
          }
        });
      }
    }
  }

  List<int> _getAvailableBranches(UserRole? role) {
    if (role == UserRole.inventoryAuditor) {
      return [1]; // Catalog only
    } else if (role == UserRole.systemAdmin) {
      return [0, 1, 3, 4]; // Dashboard, Catalog, Alerts, Analytics (no Reorder)
    } else {
      return [0, 1, 2, 3, 4]; // Store Manager sees all 5 tabs
    }
  }

  void _onTap(int navIndex) {
    final user = ref.read(currentUserProvider);
    final branches = _getAvailableBranches(user?.role);
    if (navIndex >= 0 && navIndex < branches.length) {
      final branchIndex = branches[navIndex];
      if (branchIndex == 0) {
        ref.invalidate(dashboardMetricsProvider);
      } else if (branchIndex == 3) {
        ref.invalidate(alertsProvider);
        if (user?.role == UserRole.storeManager) {
          markAllReadForStore(ref);
        }
      }
      widget.navigationShell.goBranch(
        branchIndex,
        initialLocation: branchIndex == widget.navigationShell.currentIndex,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider);
    final storesAsync = ref.watch(storesProvider);
    final activeStoreId = ref.watch(activeStoreIdProvider);
    final isManager = user?.role == UserRole.storeManager;
    final notifications = isManager ? ref.watch(notificationsStateProvider) : null;
    final unreadCount = notifications?.unreadCount ?? 0;

    return Scaffold(
      backgroundColor: context.isDarkMode ? AppColors.darkBackground : AppColors.background,
      appBar: AppBar(
        backgroundColor: context.isDarkMode ? AppColors.darkSurface : AppColors.forestGreen,
        elevation: 0,
        title: storesAsync.when(
          data: (stores) {
            final validId = stores.any((s) => s.id == activeStoreId)
                ? activeStoreId
                : stores.firstOrNull?.id;

            return DropdownButtonHideUnderline(
              child: DropdownButton<int>(
                value: validId,
                dropdownColor: context.isDarkMode ? AppColors.darkSurface : AppColors.forestGreen,
                icon: const Icon(Icons.arrow_drop_down, color: Colors.white),
                isExpanded: true,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
                items: stores.map((store) {
                  return DropdownMenuItem<int>(
                    value: store.id,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.storefront_rounded,
                          color: Colors.white,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Flexible(
                          child: Text(
                            store.name,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
                onChanged: (newStoreId) {
                  if (newStoreId != null) {
                    ref.read(activeStoreIdProvider.notifier).state = newStoreId;
                  }
                },
              ),
            );
          },
          loading: () => const Row(
            children: [
              SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              ),
              SizedBox(width: 8),
              Text(
                'Loading stores...',
                style: TextStyle(color: Colors.white, fontSize: 14),
              ),
            ],
          ),
          error: (error, stack) => const Text(
            'ZeroWaste Grocer',
            style: TextStyle(color: Colors.white, fontSize: 16),
          ),
        ),
        actions: [
          if (user != null)
            Center(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 4),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  user.role == UserRole.inventoryAuditor
                      ? 'Auditor'
                      : user.role == UserRole.systemAdmin
                          ? 'Admin'
                          : 'Manager',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          const ThemeToggleButton(),
          IconButton(
            icon: const Icon(Icons.logout_rounded, color: Colors.white),
            tooltip: 'Log Out',
            onPressed: () {
              ref.read(currentUserProvider.notifier).state = null;
              context.go('/login');
            },
          ),
        ],
      ),
      body: widget.navigationShell,
      bottomNavigationBar: user?.role == UserRole.inventoryAuditor
          ? BottomAppBar(
              height: 64,
              padding: EdgeInsets.zero,
              color: Theme.of(context).colorScheme.surface,
              surfaceTintColor: Colors.transparent,
              elevation: 2,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: const [
                    Icon(Icons.inventory_2, color: AppColors.forestGreen),
                    SizedBox(height: 4),
                    Text(
                      'Catalog',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: AppColors.forestGreen,
                      ),
                    ),
                  ],
                ),
              ),
            )
          : NavigationBar(
              selectedIndex: user?.role == UserRole.systemAdmin
                  ? (_getAvailableBranches(user?.role).contains(widget.navigationShell.currentIndex)
                      ? _getAvailableBranches(user?.role).indexOf(widget.navigationShell.currentIndex)
                      : 0)
                  : widget.navigationShell.currentIndex,
              onDestinationSelected: _onTap,
              destinations: user?.role == UserRole.systemAdmin
                  ? const [
                      NavigationDestination(
                        icon: Icon(Icons.dashboard_outlined),
                        selectedIcon: Icon(Icons.dashboard),
                        label: 'Dashboard',
                      ),
                      NavigationDestination(
                        icon: Icon(Icons.inventory_2_outlined),
                        selectedIcon: Icon(Icons.inventory_2),
                        label: 'Catalog',
                      ),
                      NavigationDestination(
                        icon: Icon(Icons.notifications_active_outlined),
                        selectedIcon: Icon(Icons.notifications_active),
                        label: 'Alerts',
                      ),
                      NavigationDestination(
                        icon: Icon(Icons.insights_outlined),
                        selectedIcon: Icon(Icons.insights),
                        label: 'Analytics',
                      ),
                    ]
                  : [
                      const NavigationDestination(
                        icon: Icon(Icons.dashboard_outlined),
                        selectedIcon: Icon(Icons.dashboard),
                        label: 'Dashboard',
                      ),
                      const NavigationDestination(
                        icon: Icon(Icons.inventory_2_outlined),
                        selectedIcon: Icon(Icons.inventory_2),
                        label: 'Catalog',
                      ),
                      const NavigationDestination(
                        icon: Icon(Icons.autorenew_outlined),
                        selectedIcon: Icon(Icons.autorenew),
                        label: 'Reorder',
                      ),
                      NavigationDestination(
                        icon: Badge(
                          isLabelVisible: isManager && unreadCount > 0,
                          label: Text(unreadCount > 9 ? '9+' : '$unreadCount'),
                          child: const Icon(Icons.notifications_active_outlined),
                        ),
                        selectedIcon: Badge(
                          isLabelVisible: isManager && unreadCount > 0,
                          label: Text(unreadCount > 9 ? '9+' : '$unreadCount'),
                          child: const Icon(Icons.notifications_active),
                        ),
                        label: 'Alerts',
                      ),
                      const NavigationDestination(
                        icon: Icon(Icons.insights_outlined),
                        selectedIcon: Icon(Icons.insights),
                        label: 'Analytics',
                      ),
                    ],
            ),
    );
  }
}
