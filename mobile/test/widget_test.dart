import 'package:cleandelivery/app.dart';
import 'package:cleandelivery/core/storage/token_storage.dart';
import 'package:cleandelivery/data/repositories/auth_repository.dart';
import 'package:cleandelivery/data/repositories/driver_repository.dart';
import 'package:cleandelivery/data/repositories/order_repository.dart';
import 'package:cleandelivery/data/repositories/product_repository.dart';
import 'package:cleandelivery/providers/auth_provider.dart';
import 'package:cleandelivery/providers/driver_provider.dart';
import 'package:cleandelivery/providers/home_provider.dart';
import 'package:cleandelivery/providers/order_provider.dart';
import 'package:cleandelivery/ui/screens/login_screen.dart';
import 'package:cleandelivery/ui/screens/home_screen.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'helpers/fake_http_adapter.dart';

/// Builds the full provider tree (same shape as [CleanDeliveryApp]) around
/// [child] using an in-memory fake HTTP adapter and mocked preferences.
Widget buildApp({
  required TokenStorage storage,
  required Dio dio,
  Widget? home,
}) {
  return MultiProvider(
    providers: [
      Provider.value(value: storage),
      Provider.value(value: dio),
      Provider<AuthRepository>(create: (_) => AuthRepository(dio: dio, storage: storage)),
      Provider<ProductRepository>(create: (_) => ProductRepository(dio: dio)),
      Provider<OrderRepository>(create: (_) => OrderRepository(dio: dio)),
      Provider<DriverRepository>(create: (_) => DriverRepository(dio: dio)),
      ChangeNotifierProvider<AuthProvider>(
        create: (context) => AuthProvider(repository: context.read<AuthRepository>()),
      ),
      ChangeNotifierProvider<HomeProvider>(
        create: (context) => HomeProvider(repository: context.read<ProductRepository>()),
      ),
      ChangeNotifierProvider<OrderProvider>(
        create: (context) => OrderProvider(repository: context.read<OrderRepository>()),
      ),
      ChangeNotifierProvider<DriverProvider>(
        create: (context) => DriverProvider(repository: context.read<DriverRepository>()),
      ),
    ],
    child: MaterialApp(home: home),
  );
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('LoginScreen', () {
    testWidgets('shows validation error for an invalid phone number', (tester) async {
      final storage = await TokenStorage.create();
      final dio = Dio(BaseOptions(baseUrl: 'http://example.test/api/v1/'))
        ..httpClientAdapter = FakeHttpAdapter({});

      await tester.pumpWidget(
        buildApp(storage: storage, dio: dio, home: const LoginScreen()),
      );
      await tester.pumpAndSettle();

      await tester.enterText(
        find.byType(TextField).at(1), // phone field
        '123',
      );
      await tester.tap(find.text('Continue'));
      await tester.pump();

      expect(find.textContaining('Enter a valid phone number'), findsOneWidget);
    });

    testWidgets('sends OTP and navigates to the OTP screen on success', (tester) async {
      SharedPreferences.setMockInitialValues({});
      final storage = await TokenStorage.create();
      final adapter = FakeHttpAdapter({
        'POST /auth/request-otp': const FakeResponse(200, {
          'message': 'OTP processed (sent)',
          'phone_number': '09123456789',
        }),
      });
      final dio = Dio(BaseOptions(baseUrl: 'http://example.test/api/v1/'))
        ..httpClientAdapter = adapter;

      await tester.pumpWidget(
        buildApp(storage: storage, dio: dio, home: const LoginScreen()),
      );
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).at(1), '09123456789');
      await tester.tap(find.text('Continue'));
      await tester.pumpAndSettle();

      expect(find.textContaining('Verify your number'), findsOneWidget);
    });
  });

  group('HomeScreen', () {
    testWidgets('renders products fetched from the API', (tester) async {
      // Provide a logged-in user so the header renders the greeting.
      const userJson =
          '{"id":"u1","phone_number":"09123456789","full_name":"Aung","role":"CUSTOMER","created_at":"2026-01-01T00:00:00Z"}';
      SharedPreferences.setMockInitialValues({'cached_user': userJson});
      final storage = await TokenStorage.create();
      final adapter = FakeHttpAdapter({
        'GET /products': const FakeResponse(200, [
          {
            'id': 'p1',
            'name': '5 Gallon',
            'price': 3500,
            'deposit_fee': 1000,
            'stock_quantity': 5,
            'created_at': '2026-01-01T00:00:00Z',
          },
          {
            'id': 'p2',
            'name': '1 Gallon',
            'price': 1200,
            'deposit_fee': 500,
            'stock_quantity': 8,
            'created_at': '2026-01-01T00:00:00Z',
          },
        ]),
      });
      final dio = Dio(BaseOptions(baseUrl: 'http://example.test/api/v1/'))
        ..httpClientAdapter = adapter;

      await tester.pumpWidget(
        buildApp(storage: storage, dio: dio, home: const HomeScreen()),
      );
      await tester.pumpAndSettle();

      expect(find.text('5 Gallon'), findsOneWidget);
      expect(find.text('1 Gallon'), findsOneWidget);
      expect(find.text('3,500 MMK'), findsOneWidget);
    });

    testWidgets('increment button updates the cart badge', (tester) async {
      SharedPreferences.setMockInitialValues({});
      final storage = await TokenStorage.create();
      final adapter = FakeHttpAdapter({
        'GET /products': const FakeResponse(200, [
          {
            'id': 'p1',
            'name': '5 Gallon',
            'price': 3500,
            'deposit_fee': 1000,
            'stock_quantity': 5,
            'created_at': '2026-01-01T00:00:00Z',
          },
        ]),
      });
      final dio = Dio(BaseOptions(baseUrl: 'http://example.test/api/v1/'))
        ..httpClientAdapter = adapter;

      await tester.pumpWidget(
        buildApp(storage: storage, dio: dio, home: const HomeScreen()),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Add'));
      await tester.pumpAndSettle();

      // Cart bar appears with the total of one unit (price + deposit).
      expect(find.text('4,500 MMK'), findsOneWidget);
      expect(find.text('Checkout'), findsOneWidget);
    });
  });
}
