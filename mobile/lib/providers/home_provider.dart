import 'package:flutter/foundation.dart';

import '../core/constants/app_constants.dart';
import '../core/errors/app_exception.dart';
import '../data/models/product.dart';
import '../data/repositories/product_repository.dart';

/// Loads the product catalogue and manages the customer's cart.
class HomeProvider extends ChangeNotifier {
  HomeProvider({required ProductRepository repository}) : _repository = repository;

  final ProductRepository _repository;

  List<Product> _products = const [];
  final Map<String, int> _cart = {};

  bool _isLoading = false;
  String? _error;
  bool _hasLoadedOnce = false;

  List<Product> get products => _products;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasLoadedOnce => _hasLoadedOnce;

  // ---- Cart ----

  int quantityOf(String productId) => _cart[productId] ?? 0;

  int get cartCount => _cart.values.fold(0, (sum, qty) => sum + qty);

  bool get hasCartItems => cartCount > 0;

  double get cartTotal {
    var total = 0.0;
    for (final product in _products) {
      final qty = quantityOf(product.id);
      if (qty > 0) {
        total += (product.price + product.depositFee) * qty;
      }
    }
    return total;
  }

  List<Product> get cartProducts =>
      _products.where((p) => quantityOf(p.id) > 0).toList();

  void increment(String productId, {int max = AppConstants.maxQuantityPerProduct}) {
    final current = quantityOf(productId);
    final stock = _productStock(productId);
    if (current >= max || (stock > 0 && current >= stock)) return;
    _cart[productId] = current + 1;
    notifyListeners();
  }

  void decrement(String productId) {
    final current = quantityOf(productId);
    if (current <= 1) {
      _cart.remove(productId);
    } else {
      _cart[productId] = current - 1;
    }
    notifyListeners();
  }

  void clearCart() {
    _cart.clear();
    notifyListeners();
  }

  int _productStock(String productId) {
    for (final product in _products) {
      if (product.id == productId) return product.stockQuantity;
    }
    return 0;
  }

  // ---- Catalogue ----

  Future<void> loadProducts({bool showLoading = true}) async {
    if (showLoading) {
      _isLoading = true;
      notifyListeners();
    }
    try {
      _products = await _repository.fetchProducts();
      _hasLoadedOnce = true;
      _error = null;
    } on AppException catch (e) {
      _error = e.message;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
