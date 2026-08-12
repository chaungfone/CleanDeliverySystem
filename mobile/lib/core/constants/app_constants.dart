/// Global application constants.
///
/// The API base URL can be overridden at build/run time with:
/// `flutter run --dart-define=API_BASE_URL=https://api.example.com/api/v1/`
class AppConstants {
  AppConstants._();

  static const String appName = 'Clean Delivery';
  static const String tagline = 'Pure water, delivered fresh';

  /// Base URL of the FastAPI backend, including the `/api/v1` prefix.
  ///
  /// Default `10.0.2.2` is the Android emulator alias for the host machine.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1/',
  );

  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);

  static const String currency = 'MMK';

  /// Maximum quantity a customer may add of a single product.
  static const int maxQuantityPerProduct = 99;
}
