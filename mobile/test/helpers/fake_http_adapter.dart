import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// A canned response for the fake HTTP adapter. [body] must be JSON-encodable
/// (a map, list, or string) and is wrapped exactly as given.
class FakeResponse {
  const FakeResponse(this.statusCode, this.body, {this.headers = const {}});

  final int statusCode;
  final dynamic body;
  final Map<String, List<String>> headers;
}

/// Minimal in-memory [HttpClientAdapter] so repositories can be tested without
/// real networking. Routes are keyed by `"METHOD /path"`.
class FakeHttpAdapter implements HttpClientAdapter {
  FakeHttpAdapter(this.routes);

  final Map<String, FakeResponse> routes;
  final List<RequestOptions> requests = [];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final key = '${options.method.toUpperCase()} ${options.path}';
    requests.add(options);
    final fake = routes[key];
    if (fake == null) {
      throw DioException.connectionError(
        requestOptions: options,
        reason: 'No fake route registered for $key',
      );
    }
    final body = fake.body == null ? '' : jsonEncode(fake.body);
    final headers = <String, List<String>>{
      Headers.contentTypeHeader: ['application/json'],
      ...fake.headers,
    };
    return ResponseBody.fromString(body, fake.statusCode, headers: headers);
  }

  @override
  void close({bool force = false}) {}
}
