import 'package:dio/dio.dart';

import '../../core/network/api_exceptions.dart';
import '../models/order.dart';

class OrderRepository {
  OrderRepository({required Dio dio}) : _dio = dio;

  final Dio _dio;

  /// Places a new order (`POST /orders`).
  Future<Order> createOrder(OrderCreateRequest request) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/orders',
        data: request.toJson(),
      );
      final data = response.data ?? const <String, dynamic>{};
      return Order.fromJson(data);
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }

  /// Fetches the order history of the current customer (`GET /orders/history`).
  Future<List<Order>> fetchOrderHistory() async {
    try {
      final response = await _dio.get<List<dynamic>>('/orders/history');
      final data = response.data ?? const [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(Order.fromJson)
          .toList();
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }

  /// Fetches a single order owned by the current customer (`GET /orders/{id}`).
  Future<Order> fetchOrder(String orderId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/orders/$orderId');
      final data = response.data ?? const <String, dynamic>{};
      return Order.fromJson(data);
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }
}
