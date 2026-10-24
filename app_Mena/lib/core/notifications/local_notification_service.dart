import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final localNotificationServiceProvider = Provider<LocalNotificationService>((ref) {
  return LocalNotificationService();
});

class LocalNotificationService {
  final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();

  bool _isInitialized = false;
  bool _permissionGranted = false;

  bool get _isAndroidSupported =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

  Future<void> init() async {
    if (!_isAndroidSupported) return;
    try {
      const androidSettings =
          AndroidInitializationSettings('@mipmap/ic_launcher');
      const initSettings = InitializationSettings(android: androidSettings);

      await _notificationsPlugin.initialize(settings: initSettings);

      // Create high-importance notification channel for Android
      const androidChannel = AndroidNotificationChannel(
        'zerowaste_alerts',
        'Spoilage Alerts',
        description: 'Automated daily spoilage markdown and risk notifications',
        importance: Importance.high,
      );

      final androidPlugin = _notificationsPlugin
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();

      if (androidPlugin != null) {
        await androidPlugin.createNotificationChannel(androidChannel);

        // Request notification permission on Android 13+ (API 33+)
        final granted = await androidPlugin.requestNotificationsPermission();
        _permissionGranted = granted ?? false;
      }

      _isInitialized = true;
    } catch (_) {
      // Swallowed silently so it never throws on any platform or configuration
    }
  }

  Future<void> show({
    required int id,
    required String title,
    required String body,
  }) async {
    if (!_isAndroidSupported || !_isInitialized || !_permissionGranted) return;
    try {
      const notificationDetails = NotificationDetails(
        android: AndroidNotificationDetails(
          'zerowaste_alerts',
          'Spoilage Alerts',
          importance: Importance.high,
          priority: Priority.high,
        ),
      );

      await _notificationsPlugin.show(
        id: id,
        title: title,
        body: body,
        notificationDetails: notificationDetails,
      );
    } catch (_) {
      // Swallowed silently so it never throws
    }
  }
}
