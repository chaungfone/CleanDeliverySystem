import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/order.dart';
import '../../../providers/driver_provider.dart';
import '../../widgets/luxury_buttons.dart';
import '../../widgets/status_chip.dart';

class DriverNavigationScreen extends StatefulWidget {
  const DriverNavigationScreen({super.key, required this.order});

  final Order order;

  @override
  State<DriverNavigationScreen> createState() => _DriverNavigationScreenState();
}

class _DriverNavigationScreenState extends State<DriverNavigationScreen> {
  bool _busy = false;
  late int _fullBottles;
  late int _emptyBottles;
  bool _codCollected = true;

  @override
  void initState() {
    super.initState();
    final total = widget.order.items.fold<int>(0, (sum, i) => sum + i.quantity);
    _fullBottles = total;
    _emptyBottles = widget.order.emptyBottlesReturned;
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _startTrip() async {
    setState(() => _busy = true);
    final ok = await context
        .read<DriverProvider>()
        .updateOrderStatus(widget.order.id, 'IN_TRANSIT');
    if (!mounted) return;
    setState(() => _busy = false);
    if (ok) {
      _showError('Trip started â€” order is now IN_TRANSIT.');
      Navigator.of(context).pop();
    } else {
      _showError(context.read<DriverProvider>().error ?? 'Could not start the trip.');
    }
  }

  Future<void> _completeDelivery() async {
    setState(() => _busy = true);
    final ok = await context
        .read<DriverProvider>()
        .updateOrderStatus(widget.order.id, 'DELIVERED');
    if (!mounted) return;
    setState(() => _busy = false);
    if (ok) {
      _showError('Delivery completed. Thank you!');
      Navigator.of(context).pop();
    } else {
      _showError(context.read<DriverProvider>().error ?? 'Could not complete the delivery.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final order = widget.order;
    final canStart = order.status.toUpperCase() == 'ASSIGNED';
    final canDeliver = !order.isCancelled && order.status.toUpperCase() != 'DELIVERED';

    return Scaffold(
      appBar: AppBar(
        title: Text('Order #${Format.shortId(order.id)}'),
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.arrow_back_rounded),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                children: [
                  _MapView(),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text('Delivery details', style: Theme.of(context).textTheme.titleMedium),
                              ),
                              StatusChip(status: order.status),
                            ],
                          ),
                          const SizedBox(height: 12),
                          _DetailRow(
                            icon: Icons.payments_outlined,
                            label: 'Total',
                            value: Format.money(order.totalAmount),
                          ),
                          _DetailRow(
                            icon: Icons.account_balance_wallet_outlined,
                            label: 'Payment',
                            value: '${order.paymentMethod} Â· ${order.paymentStatus}',
                          ),
                          _DetailRow(
                            icon: Icons.recycling_outlined,
                            label: 'Empty bottles',
                            value: '${order.emptyBottlesReturned}',
                          ),
                          _DetailRow(
                            icon: Icons.schedule_rounded,
                            label: 'Placed',
                            value: Format.dateTime(order.createdAt),
                          ),
                          const Divider(height: 20),
                          Text('Items', style: Theme.of(context).textTheme.titleSmall),
                          const SizedBox(height: 8),
                          for (final item in order.items)
                            Padding(
                              padding: const EdgeInsets.symmetric(vertical: 3),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      'Product ${item.productId.isEmpty ? '' : 'Â· '}Ã—${item.quantity}',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(fontSize: 14),
                                    ),
                                  ),
                                  Text(
                                    Format.money(item.unitPrice * item.quantity),
                                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                                  ),
                                ],
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            _buildBottomBar(context, canStart: canStart, canDeliver: canDeliver),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomBar(BuildContext context, {required bool canStart, required bool canDeliver}) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: const Border(top: BorderSide(color: AppColors.line)),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (canStart) ...[
              LuxuryButton(
                onPressed: _busy ? null : _startTrip,
                loading: _busy,
                gradient: AppColors.waterGradient,
                child: const Text('Start trip (IN_TRANSIT)'),
              ),
              const SizedBox(height: 10),
            ],
            Row(
              children: [
                _IconAction(
                  icon: Icons.call_rounded,
                  label: 'Call',
                  onTap: () => _showError('Calling the customer is not available in this build.'),
                ),
                const SizedBox(width: 10),
                _IconAction(
                  icon: Icons.chat_rounded,
                  label: 'SMS',
                  onTap: () => _showError('Messaging the customer is not available in this build.'),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: LuxuryButton(
                    onPressed: _busy || !canDeliver ? null : _openCompleteDialog,
                    height: 52,
                    gradient: AppColors.goldGradient,
                    child: const Text(
                      'Arrived',
                      style: TextStyle(color: AppColors.navy, fontWeight: FontWeight.w800),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openCompleteDialog() async {
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Complete delivery'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Verify the quantities before marking as delivered.'),
              const SizedBox(height: 18),
              _QuantityField(
                label: 'Full bottles delivered',
                value: _fullBottles,
                onChanged: (v) => setDialogState(() => _fullBottles = v),
              ),
              const SizedBox(height: 12),
              _QuantityField(
                label: 'Empty bottles collected',
                value: _emptyBottles,
                onChanged: (v) => setDialogState(() => _emptyBottles = v),
              ),
              const SizedBox(height: 12),
              CheckboxListTile(
                value: _codCollected,
                onChanged: (v) => setDialogState(() => _codCollected = v ?? true),
                title: const Text('Payment collected (COD)'),
                controlAffinity: ListTileControlAffinity.leading,
                contentPadding: EdgeInsets.zero,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.of(context).pop();
                _completeDelivery();
              },
              child: const Text('Mark as delivered'),
            ),
          ],
        ),
      ),
    );
  }
}

class _MapView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 200,
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
          Positioned.fill(
            child: CustomPaint(painter: _NavGridPainter()),
          ),
          const Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.navigation_rounded, color: AppColors.navy, size: 56),
                SizedBox(height: 6),
                Text(
                  'Live navigation view',
                  style: TextStyle(
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

class _NavGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.45)
      ..strokeWidth = 1;
    for (double x = 0; x < size.width; x += 26) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += 26) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.icon, required this.label, required this.value});

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: AppColors.muted),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 13)),
          const Spacer(),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _IconAction extends StatelessWidget {
  const _IconAction({required this.icon, required this.label, required this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        width: 58,
        height: 52,
        decoration: BoxDecoration(
          color: AppColors.canvas,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.line),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 20, color: AppColors.navy),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
          ],
        ),
      ),
    );
  }
}

class _QuantityField extends StatelessWidget {
  const _QuantityField({required this.label, required this.value, required this.onChanged});

  final String label;
  final int value;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: Text(label, style: const TextStyle(fontSize: 13))),
        IconButton.outlined(
          onPressed: () {
            if (value > 0) onChanged(value - 1);
          },
          visualDensity: VisualDensity.compact,
          icon: const Icon(Icons.remove_rounded, size: 18),
        ),
        SizedBox(
          width: 32,
          child: Text(
            '$value',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
          ),
        ),
        IconButton.outlined(
          onPressed: () => onChanged(value + 1),
          visualDensity: VisualDensity.compact,
          icon: const Icon(Icons.add_rounded, size: 18),
        ),
      ],
    );
  }
}
