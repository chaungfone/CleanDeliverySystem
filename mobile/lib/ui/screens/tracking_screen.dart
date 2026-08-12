import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../core/utils/formatters.dart';
import '../../data/models/order.dart';
import '../../providers/order_provider.dart';
import '../widgets/state_views.dart';
import '../widgets/status_chip.dart';

/// Live order tracking with a status timeline and driver card.
class TrackingScreen extends StatefulWidget {
  const TrackingScreen({super.key, required this.orderId});

  final String orderId;

  @override
  State<TrackingScreen> createState() => _TrackingScreenState();
}

class _TrackingScreenState extends State<TrackingScreen> {
  Order? _order;
  bool _loading = true;
  String? _error;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    _load();
    _pollTimer = Timer.periodic(const Duration(seconds: 12), (_) => _load(silent: true));
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent) setState(() => _loading = true);
    try {
      final order = await context.read<OrderProvider>().fetchOrder(widget.orderId);
      if (mounted) {
        setState(() {
          _order = order;
          _error = null;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = 'Unable to load the order. Pull down to retry.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final order = _order;
    return Scaffold(
      appBar: AppBar(
        title: Text(order == null ? 'Tracking' : 'Order #${Format.shortId(order.id)}'),
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.arrow_back_rounded),
        ),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _load,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [
              if (_loading && order == null)
                const SizedBox(height: 220, child: LoadingView(message: 'Locating your orderâ€¦'))
              else if (_error != null && order == null)
                SizedBox(
                  height: 300,
                  child: ErrorView(message: _error!, onRetry: _load),
                )
              else if (order != null) ...[
                _StatusTimeline(order: order),
                const SizedBox(height: 20),
                _MapPlaceholder(status: order.status),
                const SizedBox(height: 20),
                _DriverCard(order: order),
                const SizedBox(height: 20),
                _OrderSummaryCard(order: order),
                const SizedBox(height: 16),
                Center(
                  child: TextButton.icon(
                    onPressed: _loading ? null : () => _load(),
                    icon: const Icon(Icons.refresh_rounded, size: 18),
                    label: const Text('Refresh status'),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Vertical progress timeline of the order lifecycle.
class _StatusTimeline extends StatelessWidget {
  const _StatusTimeline({required this.order});

  final Order order;

  @override
  Widget build(BuildContext context) {
    final currentIndex = order.isCancelled ? 0 : order.statusIndex;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text('Order status', style: Theme.of(context).textTheme.titleMedium),
                ),
                StatusChip(status: order.status),
              ],
            ),
            const SizedBox(height: 16),
            for (var i = 0; i < Order.statusFlow.length; i++) ...[
              _TimelineStep(
                index: i,
                label: Format.orderStatusLabel(Order.statusFlow[i]),
                active: i <= currentIndex,
                isLast: i == Order.statusFlow.length - 1,
              ),
            ],
            if (order.isCancelled) ...[
              const Divider(height: 24),
              const Text(
                'This order was cancelled.',
                style: TextStyle(color: AppColors.danger, fontWeight: FontWeight.w700),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _TimelineStep extends StatelessWidget {
  const _TimelineStep({
    required this.index,
    required this.label,
    required this.active,
    required this.isLast,
  });

  final int index;
  final String label;
  final bool active;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    final color = active ? AppColors.navy : AppColors.line;
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Column(
            children: [
              Container(
                width: 26,
                height: 26,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: active ? color : Colors.transparent,
                  border: Border.all(color: color, width: 2),
                ),
                child: active
                    ? const Icon(Icons.check_rounded, color: Colors.white, size: 15)
                    : const Icon(Icons.circle, color: Colors.transparent, size: 10),
              ),
              if (!isLast)
                Container(
                  width: 2,
                  color: active ? AppColors.gold : AppColors.line,
                  margin: const EdgeInsets.symmetric(vertical: 4),
                ),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(top: 2, bottom: isLast ? 0 : 16),
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                  color: active ? AppColors.ink : AppColors.muted,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Decorative map placeholder (no Google Maps key required).
class _MapPlaceholder extends StatelessWidget {
  const _MapPlaceholder({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 180,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFD6E9F5), Color(0xFFBFE3D8)],
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Stack(
        children: [
          // Subtle grid lines to suggest a map.
          Positioned.fill(
            child: CustomPaint(painter: _MapGridPainter()),
          ),
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    gradient: AppColors.brandGradient,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.navy.withOpacity(0.3),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: const Icon(Icons.local_shipping_rounded, color: Colors.white, size: 30),
                ),
                const SizedBox(height: 12),
                Text(
                  status.toUpperCase() == 'DELIVERED'
                      ? 'Order delivered â€” enjoy!'
                      : 'Driver location appears here live',
                  style: const TextStyle(
                    color: AppColors.navySoft,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MapGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.4)
      ..strokeWidth = 1;
    for (double x = 0; x < size.width; x += 28) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += 28) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _DriverCard extends StatelessWidget {
  const _DriverCard({required this.order});

  final Order order;

  @override
  Widget build(BuildContext context) {
    final hasDriver = order.driverId != null && order.driverId!.isNotEmpty;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: const BoxDecoration(
                color: Color(0xFFE8F0FE),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.person_rounded, color: AppColors.royal, size: 28),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    hasDriver ? 'Your delivery partner' : 'Looking for a driverâ€¦',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    hasDriver
                        ? 'Driver assigned Â· will contact you on arrival'
                        : 'We are matching your order with a nearby driver.',
                    style: const TextStyle(color: AppColors.muted, fontSize: 13),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OrderSummaryCard extends StatelessWidget {
  const _OrderSummaryCard({required this.order});

  final Order order;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Order summary', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            for (final item in order.items)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${item.productId.isEmpty ? 'Product' : 'Item'} Ã—${item.quantity}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(Format.money(item.unitPrice * item.quantity)),
                  ],
                ),
              ),
            const Divider(height: 18),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Total', style: TextStyle(fontWeight: FontWeight.w800)),
                Text(
                  Format.money(order.totalAmount),
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    color: AppColors.navy,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Payment', style: TextStyle(color: AppColors.muted, fontSize: 13)),
                Text(
                  '${order.paymentMethod} Â· ${order.paymentStatus}',
                  style: const TextStyle(color: AppColors.muted, fontSize: 13),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Placed', style: TextStyle(color: AppColors.muted, fontSize: 13)),
                Text(
                  Format.dateTime(order.createdAt),
                  style: const TextStyle(color: AppColors.muted, fontSize: 13),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
