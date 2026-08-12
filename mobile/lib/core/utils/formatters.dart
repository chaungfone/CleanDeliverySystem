import 'package:intl/intl.dart';

/// Presentation helpers for money, dates and identifiers.
class Format {
  Format._();

  static final NumberFormat _number = NumberFormat('#,##0');

  /// "12,500 MMK"
  static String money(num value) => '${_number.format(value)} MMK';

  /// "1,500" (no currency suffix)
  static String number(num value) => _number.format(value);

  /// `2026-08-12T10:30:00` -> "12 Aug 2026, 10:30 AM"
  static String dateTime(String? iso) {
    final dt = DateTime.tryParse(iso ?? '');
    if (dt == null) return '—';
    return DateFormat('dd MMM yyyy, h:mm a').format(dt.toLocal());
  }

  /// `2026-08-12T10:30:00` -> "12 Aug 2026"
  static String date(String? iso) {
    final dt = DateTime.tryParse(iso ?? '');
    if (dt == null) return '—';
    return DateFormat('dd MMM yyyy').format(dt.toLocal());
  }

  /// Short human-readable id for cards: `7f3a91b2`.
  static String shortId(String id) {
    if (id.isEmpty) return '';
    return id.length <= 8 ? id : id.substring(0, 8);
  }

  /// Friendly label for an order status.
  static String orderStatusLabel(String status) {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return 'Pending';
      case 'CONFIRMED':
        return 'Confirmed';
      case 'ASSIGNED':
        return 'Driver Assigned';
      case 'IN_TRANSIT':
        return 'On the Way';
      case 'DELIVERED':
        return 'Delivered';
      case 'CANCELLED':
        return 'Cancelled';
      default:
        return status;
    }
  }
}
