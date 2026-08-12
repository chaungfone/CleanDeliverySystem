import 'dart:convert';

import 'package:cleandelivery/core/errors/app_exception.dart';
import 'package:cleandelivery/core/storage/token_storage.dart';
import 'package:cleandelivery/data/repositories/auth_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'helpers/fake_http_adapter.dart';

void main() {
  late Dio dio;
  late FakeHttpAdapter adapter;
  late TokenStorage storage;
  late AuthRepository repo;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    storage = await TokenStorage.create();
    adapter = FakeHttpAdapter({});
    dio = Dio(
      BaseOptions(baseUrl: 'http://example.test/api/v1/'),
    )..httpClientAdapter = adapter;
    repo = AuthRepository(dio: dio, storage: storage);
  });

  group('AuthRepository.requestOtp', () {
    test('sends payload and parses the response', () async {
      adapter.routes['POST /auth/request-otp'] = const FakeResponse(200, {
        'message': 'OTP processed (sent)',
        'phone_number': '09123456789',
      });

      final result = await repo.requestOtp('09123456789', fullName: 'Aung');

      expect(result.phoneNumber, '09123456789');
      expect(result.message, contains('OTP processed'));
      final body = jsonDecodeUtf8(adapter.requests.last.data);
      expect(body['phone_number'], '09123456789');
      expect(body['full_name'], 'Aung');
    });

    test('maps a 400 with a detail message to ValidationException', () async {
      adapter.routes['POST /auth/request-otp'] = const FakeResponse(400, {
        'detail': 'Phone number is not valid',
      });

      await expectLater(
        repo.requestOtp('12'),
        throwsA(isA<ValidationException>()
            .having((e) => e.message, 'message', 'Phone number is not valid')),
      );
    });

    test('maps server errors to ServerException', () async {
      adapter.routes['POST /auth/request-otp'] = const FakeResponse(500, {
        'detail': 'boom',
      });

      await expectLater(
        repo.requestOtp('09123456789'),
        throwsA(isA<ServerException>()),
      );
    });
  });

  group('AuthRepository.verifyOtp', () {
    test('persists tokens and extracts the refresh cookie', () async {
      adapter.routes['POST /auth/verify-otp'] = const FakeResponse(200, {
        'access_token': 'access-1',
        'role': 'CUSTOMER',
        'user_id': 'user-1',
      }, headers: {
        'set-cookie': ['cd_refresh_token=refresh-1; Path=/; HttpOnly'],
      });

      final auth = await repo.verifyOtp('09123456789', '123456');

      expect(auth.accessToken, 'access-1');
      expect(auth.refreshToken, 'refresh-1');
      expect(storage.accessToken, 'access-1');
      expect(storage.refreshToken, 'refresh-1');
    });

    test('surfaces the server detail when OTP is wrong', () async {
      adapter.routes['POST /auth/verify-otp'] = const FakeResponse(400, {
        'detail': 'The verification code you entered is incorrect.',
      });

      await expectLater(
        repo.verifyOtp('09123456789', '000000'),
        throwsA(isA<ValidationException>()
            .having((e) => e.message, 'message', contains('incorrect'))),
      );
    });

    test('maps 401 to UnauthorizedException', () async {
      adapter.routes['POST /auth/verify-otp'] = const FakeResponse(401, {
        'detail': 'No OTP found',
      });

      await expectLater(
        repo.verifyOtp('09123456789', '123456'),
        throwsA(isA<UnauthorizedException>()),
      );
    });
  });

  group('AuthRepository.fetchCurrentUser', () {
    test('parses user and caches it', () async {
      adapter.routes['GET /auth/me'] = const FakeResponse(200, {
        'id': 'u1',
        'phone_number': '09123456789',
        'full_name': 'Nyi Nyi',
        'role': 'DRIVER',
        'created_at': '2026-01-01T00:00:00Z',
      });

      final user = await repo.fetchCurrentUser();

      expect(user.role, 'DRIVER');
      expect(user.isDriver, isTrue);
      expect(storage.cachedUser?.fullName, 'Nyi Nyi');
    });
  });

  group('Network error mapping', () {
    test('connection errors become NetworkException', () async {
      adapter.routes.clear();
      // No route registered -> adapter throws a connection error.
      await expectLater(
        repo.requestOtp('09123456789'),
        throwsA(isA<NetworkException>()),
      );
    });
  });
}

/// Decodes a dio request body that may be a Map, String or Uint8List.
Map<String, dynamic> jsonDecodeUtf8(dynamic data) {
  if (data is Map) return Map<String, dynamic>.from(data);
  final text = data is String ? data : String.fromCharCodes(data as List<int>);
  return Map<String, dynamic>.from(jsonDecode(text) as Map);
}
