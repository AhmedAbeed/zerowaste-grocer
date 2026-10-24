/// Roles available within the ZeroWaste Grocer platform.
enum UserRole {
  storeManager,
  inventoryAuditor,
  systemAdmin,
}

/// Represents an authenticated user of the application.
class AppUser {
  const AppUser({
    required this.id,
    required this.name,
    required this.role,
    required this.token,
    this.storeId,
  });

  final String id;
  final String name;
  final UserRole role;
  final String token;
  final int? storeId;


  AppUser copyWith({
    String? id,
    String? name,
    UserRole? role,
    String? token,
    int? storeId,
  }) {
    return AppUser(
      id: id ?? this.id,
      name: name ?? this.name,
      role: role ?? this.role,
      token: token ?? this.token,
      storeId: storeId ?? this.storeId,
    );
  }
}

/// Represents a grocery retail location managed by the platform.
class Store {
  const Store({
    required this.id,
    required this.name,
    required this.location,
  });

  final int id;
  final String name;
  final String location;
}
