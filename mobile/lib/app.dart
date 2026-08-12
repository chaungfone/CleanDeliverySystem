import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/storage/token_storage.dart';
import 'core/theme/app_theme.dart';
import 'data/repositories/auth_repository.dart';
import 'data/repositories/driver_repository.dart';
import 'data/repositories/order_repository.dart';
import 'data/repositories/product_repository.dart';
import 'providers/auth_provider.dart';
import 'providers/driver_provider.dart';
import 'providers/home_provider.dart';
import 'providers/order_provider.dart';
import 'ui/navigation.dart';
import 'ui/root_gate.dart';

/// Root widget: wires dependency injection (via Provider) and the theme.
class CleanDeliveryApp extends StatelessWidget {
  const CleanDeliveryApp({super.key, required this.storage, required this.dio});

  final TokenStorage storage;
  final Dio dio;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider.value(value: storage),
        Provider.value(value: dio),
        Provider<AuthRepository>(
          create: (_) => AuthRepository(dio: dio, storage: storage),
        ),
        Provider<ProductRepository>(create: (_) => ProductRepository(dio: dio)),
        Provider<OrderRepository>(create: (_) => OrderRepository(dio: dio)),
        Provider<DriverRepository>(create: (_) => DriverRepository(dio: dio)),
        ChangeNotifierProvider<AuthProvider>(
          create: (context) => AuthProvider(
            repository: context.read<AuthRepository>(),
          ),
        ),
        ChangeNotifierProvider<HomeProvider>(
          create: (context) => HomeProvider(
            repository: context.read<ProductRepository>(),
          ),
        ),
        ChangeNotifierProvider<OrderProvider>(
          create: (context) => OrderProvider(
            repository: context.read<OrderRepository>(),
          ),
        ),
        ChangeNotifierProvider<DriverProvider>(
          create: (context) => DriverProvider(
            repository: context.read<DriverRepository>(),
          ),
        ),
      ],
      child: MaterialApp(
        title: 'Clean Delivery',
        debugShowCheckedModeBanner: false,
        navigatorKey: appNavigatorKey,
        theme: AppTheme.light(),
        darkTheme: AppTheme.dark(),
        themeMode: ThemeMode.system,
        home: const RootGate(),
      ),
    );
  }
}
