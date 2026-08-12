import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../data/models/user.dart';

/// Persists the access/refresh tokens and the last known user profile using
/// `SharedPreferences`. This mirrors the Kotlin app's `TokenManager`.
class TokenStorage {
  TokenStorage._(this._prefs);

  static const _keyAccess = 'access_token';
  static const _keyRefresh = 'refresh_token';
  static const _keyUser = 'cached_user';
  static const _keyAddress = 'last_address_text';

  final SharedPreferences _prefs;

  /// Asynchronous factory: reads the prefs once at startup.
  static Future<TokenStorage> create() async {
    final prefs = await SharedPreferences.getInstance();
    return TokenStorage._(prefs);
  }

  String? get accessToken => _prefs.getString(_keyAccess);

  String? get refreshToken => _prefs.getString(_keyRefresh);

  bool get isLoggedIn {
    final token = accessToken;
    return token != null && token.isNotEmpty;
  }

  User? get cachedUser {
    final raw = _prefs.getString(_keyUser);
    if (raw == null || raw.isEmpty) return null;
    try {
      return User.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> saveTokens(String accessToken, {String? refreshToken}) async {
    await _prefs.setString(_keyAccess, accessToken);
    if (refreshToken != null && refreshToken.isNotEmpty) {
      await _prefs.setString(_keyRefresh, refreshToken);
    }
  }

  Future<void> saveUser(User user) async {
    await _prefs.setString(_keyUser, jsonEncode(user.toJson()));
  }

  String? get lastAddressText => _prefs.getString(_keyAddress);

  Future<void> saveAddressText(String value) async {
    await _prefs.setString(_keyAddress, value);
  }

  Future<void> clear() async {
    await _prefs.remove(_keyAccess);
    await _prefs.remove(_keyRefresh);
    await _prefs.remove(_keyUser);
    await _prefs.remove(_keyAddress);
  }
}
