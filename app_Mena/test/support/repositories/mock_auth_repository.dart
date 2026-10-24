import 'package:zerowaste_grocer/features/auth/domain/models/app_user.dart';
import 'package:zerowaste_grocer/features/auth/domain/repositories/auth_repository.dart';
import '../datasources/auth_mock_datasource.dart';

class MockAuthRepository implements AuthRepository {
  MockAuthRepository({AuthMockDataSource? dataSource})
      : _dataSource = dataSource ?? AuthMockDataSource();

  final AuthMockDataSource _dataSource;

  @override
  Future<AppUser> login(String email, String password) => _dataSource.login(email, password);

  @override
  Future<List<Store>> getStores() => _dataSource.getStores();
}
