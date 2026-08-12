import 'package:flutter/foundation.dart';

import '../core/errors/app_exception.dart';
import '../data/models/order.dart';
import '../data/repositories/driver_repository.dart';

/// Holds the driver dashboard state (online status, assigned jobs, actions).
class DriverProvider extends ChangeNotifier {
  DriverProvider({required DriverRepository repository}) : _repository = repository;

  final DriverRepository _repository;

  bool _isOnline = false;
  List<Order> _orders = const [];
  bool _isLoading = false;
  String? _error;

  bool get isOnline => _isOnline;
  List<Order> get orders => _orders;
  bool get isLoading => _isLoading;
  String? get error => _error;

  int get activeJobs => _orders.where((o) => !o.isCancelled).length;

  void toggleOnline() {
    _isOnline = !_isOnline;
    _error = null;
    notifyListeners();
  }

  Future<void> loadAssignedOrders({bool showLoading = true}) async {
    if (showLoading) {
      _isLoading = true;
      notifyListeners();
    }
    try {
      _orders = await _repository.fetchAssignedOrders();
      _error = null;
    } on AppException catch (e) {
      _error = e.message;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Updates an order status and refreshes the job list.
  Future<bool> updateOrderStatus(String orderId, String status) async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      await _repository.updateOrderStatus(orderId, status);
      await _repository.fetchAssignedOrders().then((orders) {
        _orders = orders;
      });
      return true;
    } on AppException catch (e) {
      _error = e.message;
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Best-effort location report; errors are surfaced to the UI.
  Future<void> reportLocation({required double latitude, required double longitude}) async {
    try {
      await _repository.updateLocation(latitude: latitude, longitude: longitude);
    } on AppException catch (e) {
      _error = e.message;
      notifyListeners();
    }
  }

  Future<List<Map<String, dynamic>>> getOptimizedRoute({
    required double latitude,
    required double longitude,
  }) async {
    try {
      return await _repository.getOptimizedRoute(latitude: latitude, longitude: longitude);
    } on AppException catch (e) {
      _error = e.message;
      notifyListeners();
      return const [];
    }
  }
}
