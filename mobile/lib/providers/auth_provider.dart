import 'dart:async';

import 'package:flutter/foundation.dart';

import '../core/errors/app_exception.dart';
import '../core/network/dio_provider.dart';
import '../data/models/user.dart';
import '../data/repositories/auth_repository.dart';

enum AuthStatus { unknown, authenticating, authenticated, unauthenticated }

/// Holds the authentication state for the whole app.
class AuthProvider extends ChangeNotifier {
  AuthProvider({required AuthRepository repository}) : _repository = repository {
    _expirySub = SessionEvents.instance.onSessionExpired.listen((_) {
      forceLogout();
    });
  }

  final AuthRepository _repository;
  StreamSubscription<void>? _expirySub;

  AuthStatus _status = AuthStatus.unknown;
  User? _user;
  String? _error;
  bool _isLoading = false;

  AuthStatus get status => _status;
  User? get user => _user;
  String? get error => _error;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _status == AuthStatus.authenticated;

  /// Restores the session at startup using the stored token + profile.
  Future<void> init() async {
    if (_status == AuthStatus.authenticating) return;
    _status = AuthStatus.authenticating;
    _error = null;
    notifyListeners();

    if (!_repository.isLoggedIn) {
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }

    try {
      _user = await _repository.fetchCurrentUser();
      _status = AuthStatus.authenticated;
    } on UnauthorizedException {
      await _repository.logout();
      _user = null;
      _status = AuthStatus.unauthenticated;
    } on AppException catch (e) {
      // Network hiccup: fall back to the cached profile so the user is not
      // locked out while offline. The token is still present for retries.
      final cached = _repository.isLoggedIn;
      if (cached) {
        _status = AuthStatus.authenticated;
        _error = e.message;
      } else {
        _status = AuthStatus.unauthenticated;
      }
    }
    notifyListeners();
  }

  /// Sends an OTP to [phoneNumber]. Returns true on success.
  Future<bool> requestOtp(String phoneNumber, {String? fullName}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _repository.requestOtp(phoneNumber, fullName: fullName);
      return true;
    } on AppException catch (e) {
      _error = e.message;
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Verifies [otp] and loads the profile. Returns true on success.
  Future<bool> verifyOtp(String phoneNumber, String otp) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _repository.verifyOtp(phoneNumber, otp);
      _user = await _repository.fetchCurrentUser();
      _status = AuthStatus.authenticated;
      return true;
    } on AppException catch (e) {
      _error = e.message;
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    _user = null;
    _status = AuthStatus.unauthenticated;
    _error = null;
    notifyListeners();
  }

  /// Session was revoked server-side (refresh failed) — sign out silently.
  void forceLogout() {
    _user = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  void clearError() {
    if (_error != null) {
      _error = null;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _expirySub?.cancel();
    super.dispose();
  }
}
