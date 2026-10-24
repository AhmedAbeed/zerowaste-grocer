import 'package:dio/dio.dart';
import '../../domain/models/app_user.dart';
import '../models/user_model.dart';

class AuthRemoteDataSource {
  const AuthRemoteDataSource(this._dio);

  final Dio _dio;

  Future<AppUser> login(String email, String password) async {
    final response = await _dio.post(
      '/auth/login',
      data: {
        'email': email,
        'password': password,
      },
    );

    final data = response.data as Map<String, dynamic>;
    return UserModel.fromJson(data).toDomain();
  }

  Future<List<Store>> getStores() async {
    final response = await _dio.get('/stores');
    final list = response.data as List<dynamic>;
    return list
        .map((item) => StoreModel.fromJson(item as Map<String, dynamic>).toDomain())
        .toList();
  }
}
