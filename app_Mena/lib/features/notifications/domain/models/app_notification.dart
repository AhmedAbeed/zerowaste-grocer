/// Pure immutable domain entity for ZeroWaste Grocer notifications.
class AppNotification {
  const AppNotification({
    required this.id,
    required this.storeId,
    required this.type,
    required this.title,
    required this.body,
    this.batchId,
    required this.createdAt,
    required this.isRead,
  });

  final int id;
  final int storeId;
  final String type;
  final String title;
  final String body;
  final String? batchId;
  final DateTime createdAt;
  final bool isRead;



  AppNotification copyWith({
    int? id,
    int? storeId,
    String? type,
    String? title,
    String? body,
    String? batchId,
    DateTime? createdAt,
    bool? isRead,
  }) {
    return AppNotification(
      id: id ?? this.id,
      storeId: storeId ?? this.storeId,
      type: type ?? this.type,
      title: title ?? this.title,
      body: body ?? this.body,
      batchId: batchId ?? this.batchId,
      createdAt: createdAt ?? this.createdAt,
      isRead: isRead ?? this.isRead,
    );
  }
}

/// Consolidated result container holding notification items and unread count.
class NotificationsResult {
  const NotificationsResult({
    required this.items,
    required this.unreadCount,
  });

  final List<AppNotification> items;
  final int unreadCount;
}
