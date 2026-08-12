/// Application-level exceptions with user-friendly messages.
///
/// Every failure surfaced to the UI is wrapped in an [AppException] so that
/// screens only ever deal with one error type and never leak raw exceptions.
class AppException implements Exception {
  final String message;
  final int? statusCode;

  const AppException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

/// Connection-level problems: timeouts, no network, unreachable host.
class NetworkException extends AppException {
  const NetworkException([
    super.message =
        'Unable to reach the server. Please check your internet connection and try again.',
  ]);
}

/// HTTP 401 / refresh failure: the current session is no longer valid.
class UnauthorizedException extends AppException {
  const UnauthorizedException([
    super.message = 'Your session has expired. Please log in again.',
  ]);
}

/// HTTP 5xx or unexpected server behaviour.
class ServerException extends AppException {
  const ServerException([
    super.message = 'Something went wrong on our side. Please try again later.',
  ]);
}

/// HTTP 4xx validation / business-rule errors (e.g. wrong OTP, low stock).
class ValidationException extends AppException {
  const ValidationException([super.message = 'Invalid input provided.']);
}

/// Thrown when the server responds successfully but with an unexpected shape.
class ParseException extends AppException {
  const ParseException([
    super.message = 'Received an unexpected response from the server.',
  ]);
}
