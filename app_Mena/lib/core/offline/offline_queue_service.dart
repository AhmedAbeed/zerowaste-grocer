import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:hive/hive.dart';

import '../../features/catalog/data/models/catalog_models.dart';
import '../../features/catalog/domain/models/product.dart';
import '../../features/reorder/data/models/reorder_models.dart';
import '../../features/reorder/domain/models/recommendation.dart';

/// Global ScaffoldMessengerKey enabling offline alerts from anywhere
final rootScaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();

class OfflineQueueService {
  static const String approvalsBoxName = 'offline_approvals_box';
  static const String auditsBoxName = 'offline_audits_box';

  static Box<String>? get _approvalsBox =>
      Hive.isBoxOpen(approvalsBoxName) ? Hive.box<String>(approvalsBoxName) : null;

  static Box<String>? get _auditsBox =>
      Hive.isBoxOpen(auditsBoxName) ? Hive.box<String>(auditsBoxName) : null;

  static Future<void> enqueueApproval(ApprovalRequest request) async {
    final box = _approvalsBox;
    if (box != null) {
      final jsonStr = jsonEncode(ApprovalRequestModel.toJson(request));
      await box.add(jsonStr);
    }
    rootScaffoldMessengerKey.currentState?.showSnackBar(
      const SnackBar(
        content: Text('Buffered offline for synchronization'),
        backgroundColor: Colors.orange,
        duration: Duration(seconds: 3),
      ),
    );
  }

  static Future<void> enqueueAudit(int storeId, List<AuditEntry> entries) async {
    final box = _auditsBox;
    if (box != null) {
      final payload = {
        'store_id': storeId,
        'entries': entries.map((e) => AuditEntryModel.toJson(e)).toList(),
      };
      final jsonStr = jsonEncode(payload);
      await box.add(jsonStr);
    }
    rootScaffoldMessengerKey.currentState?.showSnackBar(
      const SnackBar(
        content: Text('Buffered offline for synchronization'),
        backgroundColor: Colors.orange,
        duration: Duration(seconds: 3),
      ),
    );
  }

  static Future<int> syncOfflineQueue(Dio dio) async {
    int synced = 0;

    // Flush pending approvals
    final appBox = _approvalsBox;
    if (appBox != null && appBox.isNotEmpty) {
      final keys = appBox.keys.toList();
      for (final key in keys) {
        final raw = appBox.get(key);
        if (raw != null) {
          try {
            final data = jsonDecode(raw) as Map<String, dynamic>;
            final res = await dio.post('/replenishment/approve', data: data);
            if (res.statusCode == 200 || res.statusCode == 201) {
              await appBox.delete(key);
              synced++;
            }
          } catch (_) {
            // Retain on failure
          }
        }
      }
    }

    // Flush pending audits
    final audBox = _auditsBox;
    if (audBox != null && audBox.isNotEmpty) {
      final keys = audBox.keys.toList();
      for (final key in keys) {
        final raw = audBox.get(key);
        if (raw != null) {
          try {
            final data = jsonDecode(raw) as Map<String, dynamic>;
            final res = await dio.post('/inventory/audit', data: data);
            if (res.statusCode == 200 || res.statusCode == 201) {
              await audBox.delete(key);
              synced++;
            }
          } catch (_) {
            // Retain on failure
          }
        }
      }
    }

    return synced;
  }
}
