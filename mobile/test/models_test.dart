import 'package:cleandelivery/data/models/order.dart';
import 'package:cleandelivery/data/models/product.dart';
import 'package:cleandelivery/data/models/user.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Product.fromJson', () {
    test('parses numeric prices', () {
      final product = Product.fromJson(const {
        'id': 'p1',
        'name': '5 Gallon',
        'description': 'Big bottle',
        'price': 3500,
        'deposit_fee': 1000,
        'stock_quantity': 12,
        'created_at': '2026-01-01T00:00:00Z',
      });

      expect(product.id, 'p1');
      expect(product.name, '5 Gallon');
      expect(product.price, 3500);
      expect(product.depositFee, 1000);
      expect(product.unitPriceWithDeposit, 4500);
      expect(product.stockQuantity, 12);
      expect(product.inStock, isTrue);
    });

    test('parses string (Decimal) prices defensively', () {
      final product = Product.fromJson(const {
        'id': 'p2',
        'name': '1 Gallon',
        'price': '1200.50',
        'deposit_fee': '500',
        'stock_quantity': '3',
        'created_at': '2026-01-01T00:00:00Z',
      });

      expect(product.price, closeTo(1200.5, 0.001));
      expect(product.depositFee, 500);
      expect(product.stockQuantity, 3);
    });

    test('missing fields default safely', () {
      final product = Product.fromJson(const {'id': 'p3', 'name': 'Minimal'});
      expect(product.price, 0);
      expect(product.description, isNull);
      expect(product.inStock, isFalse);
    });

    test('out of stock detection', () {
      final product = Product.fromJson(const {
        'id': 'p4',
        'name': 'Empty',
        'price': 100,
        'stock_quantity': 0,
      });
      expect(product.inStock, isFalse);
    });
  });

  group('Order.fromJson', () {
    const orderJson = {
      'id': 'ord-123',
      'customer_id': 'cust-1',
      'driver_id': 'drv-9',
      'branch_id': null,
      'address_id': 'addr-7',
      'status': 'IN_TRANSIT',
      'total_amount': '7500.00',
      'payment_status': 'PENDING',
      'payment_method': 'COD',
      'empty_bottles_returned': 2,
      'created_at': '2026-08-12T10:30:00Z',
      'items': [
        {'id': 'i1', 'order_id': 'ord-123', 'product_id': 'p1', 'quantity': 2, 'unit_price': 3500},
      ],
    };

    test('parses full order with items', () {
      final order = Order.fromJson(orderJson);
      expect(order.id, 'ord-123');
      expect(order.status, 'IN_TRANSIT');
      expect(order.totalAmount, closeTo(7500, 0.001));
      expect(order.paymentMethod, 'COD');
      expect(order.items, hasLength(1));
      expect(order.items.first.quantity, 2);
      expect(order.items.first.unitPrice, 3500);
    });

    test('status index reflects progress', () {
      expect(Order.fromJson({...orderJson, 'status': 'PENDING'}).statusIndex, 0);
      expect(Order.fromJson({...orderJson, 'status': 'DELIVERED'}).statusIndex, 4);
      expect(Order.fromJson({...orderJson, 'status': 'CANCELLED'}).isCancelled, isTrue);
    });
  });

  group('User', () {
    test('role helpers', () {
      const customer = User(
        id: '1',
        phoneNumber: '09123456789',
        fullName: 'A',
        role: 'CUSTOMER',
        createdAt: '',
      );
      const driver = User(
        id: '2',
        phoneNumber: '09123456789',
        fullName: 'B',
        role: 'driver',
        createdAt: '',
      );
      expect(customer.isDriver, isFalse);
      expect(driver.isDriver, isTrue);
      expect(customer.toJson()['phone_number'], '09123456789');
    });
  });
}
