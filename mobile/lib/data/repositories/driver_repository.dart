import 'package:dio/dio.dart';

import '../../core/network/api_exceptions.dart';
import '../models/driver_models.dart';
import '../models/order.dart';

class DriverRepository {
  DriverRepository({required Dio dio}) : _dio = dio;

  final Dio _dio;

  /// Fetches orders assigned to the current driver (`GET /drivers/orders`).
  Future<List<Order>> fetchAssignedOrders() async {
    try {
      final response = await _dio.get<List<dynamic>>('/drivers/orders');
      final data = response.data ?? const [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(Order.fromJson)
          .toList();
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }

  /// Updates an order status (`PATCH /drivers/orders/{id}/status`).
  Future<Order> updateOrderStatus(String orderId, String status) async {
    try {
      final response = await _dio.patch<Map<String, dynamic>>(
        '/drivers/orders/$orderId/status',
        data: DriverStatusUpdateRequest(status: status).toJson(),
      );
      final data = response.data ?? const <String, dynamic>{};
      return Order.fromJson(data);
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }

  /// Reports the driver's current GPS position (`POST /drivers/location`).
  Future<void> updateLocation({required double latitude, required double longitude}) async {
    try {
      await _dio.post(
        '/drivers/location',
        data: DriverLocationRequest(latitude: latitude, longitude: longitude).toJson(),
      );
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }

  /// Requests an optimised delivery sequence (`POST /drivers/optimize-route`).
  Future<List<Map<String, dynamic>>> getOptimizedRoute({
    required double latitude,
    required double longitude,
  }) async {
    try {
      final response = await _dio.get<List<dynamic>>(
        '/drivers/optimize-route',
        queryParameters: {
          'current_lat': latitude,
          'current_lng': longitude,
        },
      );
      final data = response.data ?? const [];
      return data.whereType<Map<String, dynamic>>().toList();
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }
}
