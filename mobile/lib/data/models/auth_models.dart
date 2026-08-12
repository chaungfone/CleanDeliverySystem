/// Maps the backend `app/api/v1/endpoints/auth.py` request/response bodies.
library;

/// `POST /auth/request-otp`
class RequestOtpRequest {
  final String phoneNumber;
  final String? fullName;

  const RequestOtpRequest({required this.phoneNumber, this.fullName});

  Map<String, dynamic> toJson() => {
        'phone_number': phoneNumber,
        if (fullName != null && fullName!.trim().isNotEmpty) 'full_name': fullName!.trim(),
      };
}

/// Response of `POST /auth/request-otp`.
class RequestOtpResponse {
  final String message;
  final String phoneNumber;

  /// Only present when the backend runs with `DEBUG=true`.
  final String? debugOtp;

  const RequestOtpResponse({
    required this.message,
    required this.phoneNumber,
    this.debugOtp,
  });

  factory RequestOtpResponse.fromJson(Map<String, dynamic> json) => RequestOtpResponse(
        message: json['message'] as String? ?? '',
        phoneNumber: json['phone_number'] as String? ?? '',
        debugOtp: json['debug_otp'] as String?,
      );
}

/// `POST /auth/verify-otp`
class VerifyOtpRequest {
  final String phoneNumber;
  final String otp;

  const VerifyOtpRequest({required this.phoneNumber, required this.otp});

  Map<String, dynamic> toJson() => {
        'phone_number': phoneNumber,
        'otp': otp,
      };
}

/// Response of `POST /auth/verify-otp`.
///
/// The backend issues the refresh token in an HttpOnly cookie, but a mobile
/// HTTP client cannot persist cookies. The refresh token is therefore parsed
/// from the `Set-Cookie` response header (falling back to the JSON body when
/// the backend starts returning it there too).
class AuthResponse {
  final String accessToken;
  final String? refreshToken;
  final String role;
  final String userId;

  const AuthResponse({
    required this.accessToken,
    this.refreshToken,
    required this.role,
    required this.userId,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) => AuthResponse(
        accessToken: json['access_token'] as String? ?? '',
        refreshToken: json['refresh_token'] as String?,
        role: json['role'] as String? ?? 'CUSTOMER',
        userId: json['user_id'] as String? ?? '',
      );

  bool get hasAccessToken => accessToken.isNotEmpty;
}
