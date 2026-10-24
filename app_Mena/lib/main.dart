import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'core/notifications/local_notification_service.dart';
import 'core/offline/offline_queue_service.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/theme_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Hive offline cache and settings storage
  await Hive.initFlutter();
  await Hive.openBox<String>(OfflineQueueService.approvalsBoxName);
  await Hive.openBox<String>(OfflineQueueService.auditsBoxName);
  await Hive.openBox<String>(themeSettingsBoxName);

  // Initialize Local Notifications (Android only, platform safe)
  try {
    final notificationService = LocalNotificationService();
    await notificationService.init();
  } catch (_) {
    // Suppressed to guarantee startup never fails
  }

  runApp(
    const ProviderScope(
      child: ZeroWasteGrocerApp(),
    ),
  );
}

class ZeroWasteGrocerApp extends ConsumerWidget {
  const ZeroWasteGrocerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp.router(
      title: 'ZeroWaste Grocer',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeMode,
      routerConfig: router,
      scaffoldMessengerKey: rootScaffoldMessengerKey,
    );
  }
}
