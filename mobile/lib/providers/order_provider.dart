import 'package:flutter/foundation.dart';

import '../core/errors/app_exception.dart';
import '../data/models/order.dart';
import '../data/repositories/order_repository.dart';

/// Handles checkout and order history for the customer.
class OrderProvider extends ChangeNotifier {
  OrderProvider({required OrderRepository repository}) : _repository = repository;

  final OrderRepository _repository;

  List<Order> _orders = const [];
  Order? _lastPlacedOrder;
  bool _isLoading = false;
  String? _error;

  List<Order> get orders => _orders;
  Order? get lastPlacedOrder => _lastPlacedOrder;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Places an order and remembers the result for tracking navigation.
  Future<bool> placeOrder(OrderCreateRequest request) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _lastPlacedOrder = await _repository.createOrder(request);
      return true;
    } on AppException catch (e) {
      _error = e.message;
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Loads the order history (`GET /orders/history`).
  Future<void> loadOrders({bool showLoading = true}) async {
    if (showLoading) {
      _isLoading = true;
      notifyListeners();
    }
    try {
      _orders = await _repository.fetchOrderHistory();
      _error = null;
    } on AppException catch (e) {
      _error = e.message;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetches a single order for the tracking screen.
  Future<Order> fetchOrder(String orderId) async {
    try {
      final order = await _repository.fetchOrder(orderId);
      _error = null;
      return order;
    } on AppException catch (e) {
      _error = e.message;
      rethrow;
    }
  }

  /// Address id of the most recently known order, if any (used at checkout).
  String? get lastUsedAddressId {
    if (_orders.isEmpty) return null;
    final latest = _orders.firstWhere(
      (o) => o.addressId.isNotEmpty,
      orElse: () => _orders.first,
    );
    return latest.addressId.isNotEmpty ? latest.addressId : null;
  }

  void clearError() {
    if (_error != null) {
      _error = null;
      notifyListeners();
    }
  }
}
