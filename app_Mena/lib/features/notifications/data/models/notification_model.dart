import '../../domain/models/app_notification.dart';

class NotificationModel {
  const NotificationModel({
    required this.id,
    required this.storeId,
    required this.type,
    required this.title,
    required this.body,
    this.batchId,
    required this.createdAt,
    required this.isRead,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: (json['id'] as num).toInt(),
      storeId: (json['store_id'] as num).toInt(),
      type: json['type'] as String? ?? 'SPOILAGE_MARKDOWN',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      batchId: json['batch_id']?.toString(),
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
      isRead: json['is_read'] as bool? ?? false,
    );
  }

  final int id;
  final int storeId;
  final String type;
  final String title;
  final String body;
  final String? batchId;
  final DateTime createdAt;
  final bool isRead;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'store_id': storeId,
      'type': type,
      'title': title,
      'body': body,
      'batch_id': batchId,
      'created_at': createdAt.toIso8601String(),
      'is_read': isRead,
    };
  }

  AppNotification toDomain() {
    return AppNotification(
      id: id,
      storeId: storeId,
      type: type,
      title: title,
      body: body,
      batchId: batchId,
      createdAt: createdAt,
      isRead: isRead,
    );
  }
}

class NotificationsListModel {
  const NotificationsListModel({
    required this.items,
    required this.unreadCount,
  });

  factory NotificationsListModel.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return NotificationsListModel(
      items: rawItems
          .map((item) => NotificationModel.fromJson(item as Map<String, dynamic>).toDomain())
          .toList(),
      unreadCount: (json['unread_count'] as num?)?.toInt() ?? 0,
    );
  }

  final List<AppNotification> items;
  final int unreadCount;

  NotificationsResult toDomain() {
    return NotificationsResult(
      items: items,
      unreadCount: unreadCount,
    );
  }
}
