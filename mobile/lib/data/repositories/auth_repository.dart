import 'package:dio/dio.dart';

import '../../core/errors/app_exception.dart';
import '../../core/network/api_exceptions.dart';
import '../../core/storage/token_storage.dart';
import '../models/auth_models.dart';
import '../models/user.dart';

/// Data access for the auth domain.
///
/// All network errors are converted to [AppException]s before reaching the UI.
class AuthRepository {
  AuthRepository({required Dio dio, required TokenStorage storage})
      : _dio = dio,
        _storage = storage;

  final Dio _dio;
  final TokenStorage _storage;

  bool get isLoggedIn => _storage.isLoggedIn;

  /// Requests an OTP for the given phone number.
  Future<RequestOtpResponse> requestOtp(String phoneNumber, {String? fullName}) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/auth/request-otp',
        data: RequestOtpRequest(phoneNumber: phoneNumber, fullName: fullName).toJson(),
      );
      final data = response.data ?? const <String, dynamic>{};
      return RequestOtpResponse.fromJson(data);
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }

  /// Verifies the OTP and persists the returned tokens.
  ///
  /// The backend puts the refresh token into an HttpOnly `Set-Cookie` header,
  /// so it is extracted from the header when the JSON body does not include it.
  Future<AuthResponse> verifyOtp(String phoneNumber, String otp) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/auth/verify-otp',
        data: VerifyOtpRequest(phoneNumber: phoneNumber, otp: otp).toJson(),
      );
      final data = response.data ?? const <String, dynamic>{};
      var auth = AuthResponse.fromJson(data);

      if (auth.refreshToken == null) {
        auth = AuthResponse(
          accessToken: auth.accessToken,
          refreshToken: _extractRefreshCookie(response),
          role: auth.role,
          userId: auth.userId,
        );
      }
      if (!auth.hasAccessToken) {
        throw const ValidationException('Verification failed. Please try again.');
      }
      await _storage.saveTokens(auth.accessToken, refreshToken: auth.refreshToken);
      return auth;
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }

  /// Fetches the currently authenticated user profile (`GET /auth/me`).
  Future<User> fetchCurrentUser() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/auth/me');
      final data = response.data ?? const <String, dynamic>{};
      final user = User.fromJson(data);
      await _storage.saveUser(user);
      return user;
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }

  Future<void> logout() => _storage.clear();

  /// Parses `cd_refresh_token` out of a `Set-Cookie` header value.
  static String? _extractRefreshCookie(Response<dynamic> response) {
    final setCookies = response.headers['set-cookie'];
    if (setCookies == null) return null;
    for (final raw in setCookies) {
      for (final part in raw.split(';')) {
        final pair = part.trim();
        if (pair.startsWith('cd_refresh_token=')) {
          final value = pair.substring('cd_refresh_token='.length).trim();
          if (value.isNotEmpty) return value;
        }
      }
    }
    return null;
  }
}
