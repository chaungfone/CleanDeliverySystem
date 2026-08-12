import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../data/models/order.dart';
import '../../../providers/driver_provider.dart';
import '../../widgets/status_chip.dart';
import 'driver_navigation_screen.dart';

class DeliveryListScreen extends StatefulWidget {
  const DeliveryListScreen({super.key});

  @override
  State<DeliveryListScreen> createState() => _DeliveryListScreenState();
}

class _DeliveryListScreenState extends State<DeliveryListScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DriverProvider>().loadAssignedOrders();
    });
  }

  Future<void> _refresh() => context.read<DriverProvider>().loadAssignedOrders(showLoading: false);

  @override
  Widget build(BuildContext context) {
    final driver = context.watch<DriverProvider>();
    final orders = driver.orders;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Delivery jobs'),
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.arrow_back_rounded),
        ),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _refresh,
          child: orders.isEmpty && !driver.isLoading
              ? ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: const [
                    SizedBox(height: 120),
                    Icon(Icons.hourglass_empty_rounded, size: 64, color: AppColors.muted),
                    SizedBox(height: 12),
                    Center(child: Text('No delivery jobs assigned right now.')),
                  ],
                )
              : ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  itemCount: orders.length + (driver.isLoading ? 1 : 0),
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    if (index >= orders.length) {
                      return const Center(
                        child: Padding(
                          padding: EdgeInsets.all(12),
                          child: CircularProgressIndicator(strokeWidth: 2.5),
                        ),
                      );
                    }
                    return DeliveryJobCard(
                      order: orders[index],
                      onOpen: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => DriverNavigationScreen(order: orders[index]),
                          ),
                        );
                      },
                    );
                  },
                ),
        ),
      ),
    );
  }
}

class DeliveryJobCard extends StatelessWidget {
  const DeliveryJobCard({super.key, required this.order, required this.onOpen});

  final Order order;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F0FE),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.location_on_rounded, color: AppColors.royal, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Order #${Format.shortId(order.id)}',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        Format.dateTime(order.createdAt),
                        style: const TextStyle(color: AppColors.muted, fontSize: 12),
                      ),
                    ],
                  ),
                ),
                StatusChip(status: order.status),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              order.items.map((i) => '${i.quantity}Ã—').join(' Â· '),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 13, color: AppColors.muted),
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.payments_outlined, size: 16, color: AppColors.muted),
                const SizedBox(width: 6),
                Text(
                  '${Format.money(order.totalAmount)} Â· ${order.paymentMethod}',
                  style: const TextStyle(fontSize: 13, color: AppColors.muted),
                ),
                const Spacer(),
                Text(
                  '${order.emptyBottlesReturned} empty',
                  style: const TextStyle(fontSize: 13, color: AppColors.muted),
                ),
              ],
            ),
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: onOpen,
                icon: const Icon(Icons.navigation_rounded, size: 18),
                label: Text(
                  order.status.toUpperCase() == 'DELIVERED'
                      ? 'View details'
                      : 'Start delivery',
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
