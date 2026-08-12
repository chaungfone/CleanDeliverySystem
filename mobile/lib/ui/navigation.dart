import 'package:flutter/material.dart';

/// Root navigator key, used to reset the navigation stack on session changes.
final GlobalKey<NavigatorState> appNavigatorKey = GlobalKey<NavigatorState>();

/// Pushes [route] and replaces the whole stack so that back never returns to
/// auth screens after login.
void pushAndReplaceStack(BuildContext context, Widget route) {
  Navigator.of(context).pushAndRemoveUntil(
    MaterialPageRoute(builder: (_) => route),
    (route) => false,
  );
}

/// Resets the navigation stack to its first route (used on session expiry).
void resetNavigationStack() {
  final navigator = appNavigatorKey.currentState;
  if (navigator != null) {
    navigator.popUntil((route) => route.isFirst);
  }
}
