import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../constants/app_constants.dart';
import '../storage/token_storage.dart';

/// Broadcast stream fired when the refresh token can no longer be rotated
/// (expired / revoked), so the auth layer can sign the user out.
class SessionEvents {
  SessionEvents._();
  static final SessionEvents instance = SessionEvents._();

  final _controller = StreamController<void>.broadcast();
  Stream<void> get onSessionExpired => _controller.stream;

  void notifySessionExpired() {
    if (!_controller.isClosed) {
      _controller.add(null);
    }
  }
}

/// Builds the app-wide [Dio] instance wired with authentication and token
/// refresh interceptors.
Dio createDio({required TokenStorage storage}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: AppConstants.connectTimeout,
      receiveTimeout: AppConstants.receiveTimeout,
      headers: const {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ),
  );

  final refresher = TokenRefresher(storage: storage, dio: dio);

  dio.interceptors.add(_AuthInterceptor(storage));
  dio.interceptors.add(_RefreshInterceptor(storage: storage, refresher: refresher));

  if (kDebugMode) {
    dio.interceptors.add(
      LogInterceptor(requestBody: true, responseBody: true, logPrint: (o) => debugPrint(o.toString())),
    );
  }

  return dio;
}

/// Attaches the stored JWT to every authenticated request.
class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._storage);

  final TokenStorage _storage;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = _storage.accessToken;
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}

/// On a 401 response, attempts a single-flight token refresh and retries the
/// failed request. When refresh fails, the session is cleared and the UI is
/// notified so the user is returned to the login screen.
class _RefreshInterceptor extends Interceptor {
  _RefreshInterceptor({required TokenStorage storage, required TokenRefresher refresher})
      : _storage = storage,
        _refresher = refresher;

  static const _retryHeader = 'X-Retry-After-Refresh';
  final TokenStorage _storage;
  final TokenRefresher _refresher;

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final status = err.response?.statusCode;
    final path = err.requestOptions.path;

    // Only intercept 401s on authenticated endpoints.
    final isAuthRequest =
        path.contains('/auth/request-otp') ||
        path.contains('/auth/verify-otp') ||
        path.contains('/auth/refresh');
    final alreadyRetried = err.requestOptions.headers[_retryHeader] == '1';

    if (status != 401 || isAuthRequest || alreadyRetried) {
      handler.next(err);
      return;
    }

    final refreshed = await _refresher.refresh();
    if (!refreshed) {
      handler.next(err);
      return;
    }

    // Retry once with the freshly rotated access token.
    final options = err.requestOptions;
    options.headers[_retryHeader] = '1';
    options.headers['Authorization'] = 'Bearer ${_storage.accessToken}';
    try {
      final response = await _refresher.dio.fetch(options);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }
}

/// Performs a single-flight refresh of the access token via
/// `POST /auth/refresh` (mobile JSON flow). Concurrent 401s share one refresh
/// request and all waiters reuse the rotated token.
class TokenRefresher {
  TokenRefresher({required TokenStorage storage, required this.dio})
      : _storage = storage;

  final TokenStorage _storage;
  final Dio dio;

  Future<bool>? _inFlight;

  Future<bool> refresh() {
    final current = _inFlight;
    if (current != null) return current;

    final future = _doRefresh();
    _inFlight = future.whenComplete(() => _inFlight = null);
    return _inFlight!;
  }

  Future<bool> _doRefresh() async {
    final refreshToken = _storage.refreshToken;
    if (refreshToken == null || refreshToken.isEmpty) {
      _expireSession();
      return false;
    }

    try {
      final response = await dio.post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
        options: Options(headers: const {'X-Client-Type': 'mobile'}),
      );
      final data = response.data;
      if (data is! Map<String, dynamic>) {
        _expireSession();
        return false;
      }
      final access = data['access_token'];
      if (access is! String || access.isEmpty) {
        _expireSession();
        return false;
      }
      final rotatedRefresh = data['refresh_token'];
      await _storage.saveTokens(
        access,
        refreshToken: rotatedRefresh is String && rotatedRefresh.isNotEmpty
            ? rotatedRefresh
            : refreshToken,
      );
      return true;
    } on DioException catch (error) {
      // 401/400 => refresh token is dead; otherwise keep the session and let
      // the original error propagate (e.g. temporary network failure).
      final status = error.response?.statusCode;
      if (status == 401 || status == 403 || status == 400) {
        _expireSession();
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  void _expireSession() {
    _storage.clear();
    SessionEvents.instance.notifySessionExpired();
  }
}
