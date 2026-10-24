import '../../domain/models/app_user.dart';

class UserModel {
  const UserModel({
    required this.id,
    required this.name,
    required this.role,
    required this.token,
    this.storeId,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    // Handles both {"token": ..., "user": {...}} and flat user JSON
    final userJson = json.containsKey('user') && json['user'] is Map<String, dynamic>
        ? json['user'] as Map<String, dynamic>
        : json;

    final token = json['token'] as String? ?? userJson['token'] as String? ?? '';
    final id = userJson['id']?.toString() ?? '';
    final name = userJson['name'] as String? ?? '';
    final roleStr = userJson['role'] as String? ?? 'storeManager';
    final storeId = (userJson['store_id'] as num?)?.toInt() ?? (json['store_id'] as num?)?.toInt();

    UserRole role;
    switch (roleStr.toLowerCase()) {
      case 'inventoryauditor':
      case 'auditor':
        role = UserRole.inventoryAuditor;
        break;
      case 'systemadmin':
      case 'admin':
        role = UserRole.systemAdmin;
        break;
      case 'storemanager':
      case 'manager':
      default:
        role = UserRole.storeManager;
        break;
    }

    return UserModel(
      id: id,
      name: name,
      role: role,
      token: token,
      storeId: storeId,
    );
  }

  final String id;
  final String name;
  final UserRole role;
  final String token;
  final int? storeId;


  AppUser toDomain() {
    return AppUser(
      id: id,
      name: name,
      role: role,
      token: token,
      storeId: storeId,
    );
  }
}

class StoreModel {
  const StoreModel({
    required this.id,
    required this.name,
    required this.location,
  });

  factory StoreModel.fromJson(Map<String, dynamic> json) {
    return StoreModel(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String? ?? '',
      location: json['location'] as String? ?? '',
    );
  }

  final int id;
  final String name;
  final String location;

  Store toDomain() {
    return Store(
      id: id,
      name: name,
      location: location,
    );
  }
}
