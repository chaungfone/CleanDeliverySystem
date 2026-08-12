import 'package:dio/dio.dart';

import '../../core/network/api_exceptions.dart';
import '../models/product.dart';

class ProductRepository {
  ProductRepository({required Dio dio}) : _dio = dio;

  final Dio _dio;

  /// Fetches the product catalogue (`GET /products`).
  Future<List<Product>> fetchProducts() async {
    try {
      final response = await _dio.get<List<dynamic>>('/products');
      final data = response.data ?? const [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(Product.fromJson)
          .toList();
    } on DioException catch (error) {
      throw mapDioException(error);
    }
  }
}
