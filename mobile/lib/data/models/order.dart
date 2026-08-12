/// Maps the backend `app/models/order.py` schemas.
///
/// `status`: PENDING | CONFIRMED | ASSIGNED | IN_TRANSIT | DELIVERED | CANCELLED.
/// `payment_method`: COD | KPAY | WAVE_PAY | OTHER.
library;

/// `POST /orders` body.
class OrderCreateRequest {
  final String addressId;
  final String paymentMethod;
  final int emptyBottlesReturned;
  final List<OrderItemCreateRequest> items;

  const OrderCreateRequest({
    required this.addressId,
    this.paymentMethod = 'COD',
    this.emptyBottlesReturned = 0,
    required this.items,
  });

  Map<String, dynamic> toJson() => {
        'address_id': addressId,
        'payment_method': paymentMethod,
        'empty_bottles_returned': emptyBottlesReturned,
        'items': items.map((e) => e.toJson()).toList(),
      };
}

class OrderItemCreateRequest {
  final String productId;
  final int quantity;
  final double? unitPrice;

  const OrderItemCreateRequest({
    required this.productId,
    required this.quantity,
    this.unitPrice,
  });

  Map<String, dynamic> toJson() => {
        'product_id': productId,
        'quantity': quantity,
        if (unitPrice != null) 'unit_price': unitPrice,
      };
}

class OrderItem {
  final String id;
  final String orderId;
  final String productId;
  final int quantity;
  final double unitPrice;

  const OrderItem({
    required this.id,
    required this.orderId,
    required this.productId,
    required this.quantity,
    required this.unitPrice,
  });

  factory OrderItem.fromJson(Map<String, dynamic> json) => OrderItem(
        id: json['id'] as String? ?? '',
        orderId: json['order_id'] as String? ?? '',
        productId: json['product_id'] as String? ?? '',
        quantity: _asInt(json['quantity']),
        unitPrice: _asDouble(json['unit_price']),
      );

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

class Order {
  final String id;
  final String customerId;
  final String? driverId;
  final String? branchId;
  final String addressId;
  final String status;
  final double totalAmount;
  final String paymentStatus;
  final String paymentMethod;
  final int emptyBottlesReturned;
  final String createdAt;
  final List<OrderItem> items;

  const Order({
    required this.id,
    required this.customerId,
    this.driverId,
    this.branchId,
    required this.addressId,
    required this.status,
    required this.totalAmount,
    required this.paymentStatus,
    required this.paymentMethod,
    this.emptyBottlesReturned = 0,
    required this.createdAt,
    this.items = const [],
  });

  factory Order.fromJson(Map<String, dynamic> json) => Order(
        id: json['id'] as String? ?? '',
        customerId: json['customer_id'] as String? ?? '',
        driverId: json['driver_id'] as String?,
        branchId: json['branch_id'] as String?,
        addressId: json['address_id'] as String? ?? '',
        status: json['status'] as String? ?? 'PENDING',
        totalAmount: _asDouble(json['total_amount']),
        paymentStatus: json['payment_status'] as String? ?? 'PENDING',
        paymentMethod: json['payment_method'] as String? ?? 'COD',
        emptyBottlesReturned: _asInt(json['empty_bottles_returned']),
        createdAt: json['created_at'] as String? ?? '',
        items: (json['items'] as List<dynamic>? ?? [])
            .whereType<Map<String, dynamic>>()
            .map(OrderItem.fromJson)
            .toList(),
      );

  /// Order status order used to render the tracking timeline.
  static const List<String> statusFlow = [
    'PENDING',
    'CONFIRMED',
    'ASSIGNED',
    'IN_TRANSIT',
    'DELIVERED',
  ];

  int get statusIndex {
    final idx = statusFlow.indexOf(status.toUpperCase());
    return idx < 0 ? 0 : idx;
  }

  bool get isCancelled => status.toUpperCase() == 'CANCELLED';

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
