import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import 'screens/driver/driver_home_screen.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/splash_screen.dart';

/// Decides which screen to show based on the authentication state.
class RootGate extends StatefulWidget {
  const RootGate({super.key});

  @override
  State<RootGate> createState() => _RootGateState();
}

class _RootGateState extends State<RootGate> {
  AuthStatus? _lastStatus;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<AuthProvider>().init();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final status = auth.status;

    // When the session changes between logged-in / logged-out, clear any
    // pushed routes so the new root screen is always visible.
    if (_lastStatus != null &&
        _lastStatus != status &&
        (status == AuthStatus.authenticated || status == AuthStatus.unauthenticated)) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final navigator = Navigator.of(context);
        if (navigator.canPop()) navigator.popUntil((route) => route.isFirst);
      });
    }
    _lastStatus = status;

    return switch (status) {
      AuthStatus.unknown ||
      AuthStatus.authenticating =>
        const SplashScreen(),
      AuthStatus.unauthenticated => const LoginScreen(),
      AuthStatus.authenticated =>
        (auth.user?.isDriver ?? false) ? const DriverHomeScreen() : const HomeScreen(),
    };
  }
}
