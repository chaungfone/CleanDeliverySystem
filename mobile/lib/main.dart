import 'package:flutter/material.dart';

import 'app.dart';
import 'core/network/dio_provider.dart';
import 'core/storage/token_storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Restore persisted tokens before the UI builds so the root gate can decide
  // the start screen without flashing the login page.
  final storage = await TokenStorage.create();
  final dio = createDio(storage: storage);

  runApp(CleanDeliveryApp(storage: storage, dio: dio));
}
