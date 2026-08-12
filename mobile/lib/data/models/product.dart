/// Maps the backend `app/models/product.py::ProductResponse`.
///
/// FastAPI may serialise `Decimal` prices either as JSON numbers or strings
/// depending on configuration, so the parser accepts both.
class Product {
  final String id;
  final String name;
  final String? description;
  final double price;
  final double depositFee;
  final int stockQuantity;
  final String createdAt;

  const Product({
    required this.id,
    required this.name,
    this.description,
    required this.price,
    this.depositFee = 0,
    this.stockQuantity = 0,
    required this.createdAt,
  });

  factory Product.fromJson(Map<String, dynamic> json) => Product(
        id: json['id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        description: json['description'] as String?,
        price: _asDouble(json['price']),
        depositFee: _asDouble(json['deposit_fee']),
        stockQuantity: _asInt(json['stock_quantity']),
        createdAt: json['created_at'] as String? ?? '',
      );

  bool get inStock => stockQuantity > 0;

  /// Unit price including the bottle deposit fee.
  double get unitPriceWithDeposit => price + depositFee;

  static double _asDouble(dynamic value) {
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0;
    return 0;
  }

  static int _asInt(dynamic value) {
    if (value is num) return value.toInt();
    if (value is String) return int.tryParse(value) ?? 0;
    return 0;
  }
}
