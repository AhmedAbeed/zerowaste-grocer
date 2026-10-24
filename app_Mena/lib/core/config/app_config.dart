import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Central configuration file for ZeroWaste Grocer.
///
/// Controls environment settings, API base URL, and network timeouts.
class AppConfig {
  AppConfig({
    String? baseUrl,
    this.connectTimeout = const Duration(seconds: 15),
    this.receiveTimeout = const Duration(seconds: 15),
  }) : baseUrl = baseUrl ?? defaultBaseUrl;

  /// Base URL for the backend REST APIs (/api/v1).
  final String baseUrl;

  /// Dio connect timeout duration.
  final Duration connectTimeout;

  /// Dio receive timeout duration.
  final Duration receiveTimeout;

  static String get defaultBaseUrl {
    if (kIsWeb) return 'http://127.0.0.1:8000/api/v1';
    if (Platform.isAndroid) return 'http://10.0.2.2:8000/api/v1';
    return 'http://127.0.0.1:8000/api/v1';
  }
}

/// Global provider for AppConfig
final appConfigProvider = Provider<AppConfig>((ref) {
  return AppConfig();
});
