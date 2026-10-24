import 'package:dio/dio.dart';
import '../../domain/models/app_user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_datasource.dart';

class RemoteAuthRepository implements AuthRepository {
  RemoteAuthRepository({AuthRemoteDataSource? remoteDataSource, Dio? dio})
      : _remoteDataSource = remoteDataSource ?? AuthRemoteDataSource(dio ?? Dio());

  final AuthRemoteDataSource _remoteDataSource;

  @override
  Future<AppUser> login(String email, String password) {
    return _remoteDataSource.login(email, password);
  }

  @override
  Future<List<Store>> getStores() {
    return _remoteDataSource.getStores();
  }
}
