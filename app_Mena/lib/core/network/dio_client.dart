import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/app_config.dart';
import '../../features/auth/presentation/auth_providers.dart';

/// Provider exposing configured Dio client for backend communication
final dioProvider = Provider<Dio>((ref) {
  final config = ref.watch(appConfigProvider);

  final dio = Dio(
    BaseOptions(
      baseUrl: config.baseUrl,
      connectTimeout: config.connectTimeout,
      receiveTimeout: config.receiveTimeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) {
        final currentUser = ref.read(currentUserProvider);
        if (currentUser != null && currentUser.token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer ${currentUser.token}';
        }
        if (kDebugMode) {
          debugPrint('--> ${options.method} ${options.uri}');
        }
        return handler.next(options);
      },
      onResponse: (response, handler) {
        if (kDebugMode) {
          debugPrint('<-- ${response.statusCode} ${response.requestOptions.uri}');
        }
        return handler.next(response);
      },
      onError: (DioException error, handler) {
        if (kDebugMode) {
          debugPrint('<-- ERROR ${error.response?.statusCode}: ${error.message} (${error.requestOptions.uri})');
        }
        return handler.next(error);
      },
    ),
  );

  return dio;
});
