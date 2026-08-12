import 'package:cleandelivery/core/utils/formatters.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Format.money', () {
    test('groups thousands and appends MMK', () {
      expect(Format.money(0), '0 MMK');
      expect(Format.money(500), '500 MMK');
      expect(Format.money(12500), '12,500 MMK');
      expect(Format.money(12500.5), '12,501 MMK');
    });
  });

  group('Format.shortId', () {
    test('truncates long ids', () {
      expect(Format.shortId(''), '');
      expect(Format.shortId('abc'), 'abc');
      expect(Format.shortId('1234567890abcdef'), '12345678');
    });
  });

  group('Format.orderStatusLabel', () {
    test('maps status codes to friendly labels', () {
      expect(Format.orderStatusLabel('PENDING'), 'Pending');
      expect(Format.orderStatusLabel('IN_TRANSIT'), 'On the Way');
      expect(Format.orderStatusLabel('DELIVERED'), 'Delivered');
      expect(Format.orderStatusLabel('WEIRD'), 'WEIRD');
    });
  });

  group('Format.dateTime', () {
    test('formats iso strings', () {
      expect(Format.dateTime('2026-08-12T10:30:00Z'), isNotEmpty);
      expect(Format.dateTime(null), '—');
      expect(Format.dateTime('not-a-date'), '—');
    });
  });
}
