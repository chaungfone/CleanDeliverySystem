import 'package:dio/dio.dart';

import '../errors/app_exception.dart';

/// Maps a [DioException] to an [AppException] with a user-friendly message.
AppException mapDioException(DioException error) {
  switch (error.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
    case DioExceptionType.transformTimeout:
      return const NetworkException(
        'The connection timed out. Please try again.',
      );
    case DioExceptionType.connectionError:
      return const NetworkException(
        'No internet connection. Please check your network and try again.',
      );
    case DioExceptionType.badCertificate:
      return const NetworkException('A secure connection could not be verified.');
    case DioExceptionType.cancel:
      return const NetworkException('The request was cancelled.');
    case DioExceptionType.badResponse:
      final status = error.response?.statusCode;
      final message = _extractServerMessage(error.response?.data);
      if (status == 401) {
        return UnauthorizedException(message ?? 'Your session has expired. Please log in again.');
      }
      if (status != null && status >= 500) {
        return ServerException(message ?? 'The server is temporarily unavailable. Please try again later.');
      }
      return ValidationException(message ?? 'The request could not be completed (HTTP $status).');
    case DioExceptionType.unknown:
      return NetworkException(error.message ?? 'An unexpected error occurred.');
  }
}

/// Extracts a human-readable message from common backend error bodies:
/// `{"detail": "..."}` (FastAPI) or `{"message": "..."}`.
String? _extractServerMessage(dynamic data) {
  if (data is Map) {
    final detail = data['detail'];
    if (detail is String && detail.trim().isNotEmpty) return detail;
    if (detail is Map) {
      final d = detail['message'];
      if (d is String && d.trim().isNotEmpty) return d;
    }
    final message = data['message'];
    if (message is String && message.trim().isNotEmpty) return message;
    final msg = data['msg'];
    if (msg is String && msg.trim().isNotEmpty) return msg;
  }
  return null;
}
