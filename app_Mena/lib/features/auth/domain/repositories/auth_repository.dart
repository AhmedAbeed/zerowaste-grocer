import '../models/app_user.dart';

abstract class AuthRepository {
  Future<AppUser> login(String email, String password);
  Future<List<Store>> getStores();
}
