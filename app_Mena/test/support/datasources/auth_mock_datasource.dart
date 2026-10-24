import '../mock_database.dart';
import 'package:zerowaste_grocer/features/auth/domain/models/app_user.dart';

class AuthMockDataSource {
  final MockDatabase _db = MockDatabase.instance;

  Future<AppUser> login(String email, String password) async {
    await Future.delayed(const Duration(milliseconds: 400));
    final role = email.contains('auditor')
        ? UserRole.inventoryAuditor
        : email.contains('admin')
            ? UserRole.systemAdmin
            : UserRole.storeManager;

    return AppUser(
      id: 'USR-001',
      name: 'Mena Mikhail',
      role: role,
      token: 'jwt_mock_token_mena_zerowaste_${DateTime.now().millisecondsSinceEpoch}',
    );
  }

  Future<List<Store>> getStores() async {
    await Future.delayed(const Duration(milliseconds: 400));
    return _db.getStores();
  }
}
