import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../providers/driver_provider.dart';
import '../../widgets/state_views.dart';
import '../../widgets/status_chip.dart';

class EarningsScreen extends StatefulWidget {
  const EarningsScreen({super.key});

  @override
  State<EarningsScreen> createState() => _EarningsScreenState();
}

class _EarningsScreenState extends State<EarningsScreen> {
  @override
  Widget build(BuildContext context) {
    final driver = context.watch<DriverProvider>();
    final jobsDelivered = driver.orders
        .where((o) => o.status.toUpperCase() == 'DELIVERED')
        .length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Earnings & history'),
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.arrow_back_rounded),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Container(
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                gradient: AppColors.brandGradient,
                borderRadius: BorderRadius.circular(22),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.navy.withOpacity(0.3),
                    blurRadius: 20,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'TOTAL BALANCE',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.4,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    '0 MMK',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 32,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.14),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Text(
                      'Delivered jobs: $jobsDelivered',
                      style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const SectionHeader(title: 'Recent deliveries'),
            const SizedBox(height: 12),
            if (driver.isLoading)
              const SizedBox(height: 120, child: LoadingView())
            else if (driver.orders.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Text(
                    'No deliveries yet. Your completed jobs will appear here.',
                    textAlign: TextAlign.center,
                  ),
                ),
              )
            else
              for (final order in driver.orders)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Card(
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: order.status.toUpperCase() == 'DELIVERED'
                            ? const Color(0xFFDCFCE7)
                            : const Color(0xFFE2E8F0),
                        child: Icon(
                          order.status.toUpperCase() == 'DELIVERED'
                              ? Icons.check_rounded
                              : Icons.schedule_rounded,
                          color: order.status.toUpperCase() == 'DELIVERED'
                              ? AppColors.success
                              : AppColors.muted,
                          size: 20,
                        ),
                      ),
                      title: Text('Order #${Format.shortId(order.id)}'),
                      subtitle: Text(Format.dateTime(order.createdAt)),
                      trailing: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            Format.money(order.totalAmount),
                            style: const TextStyle(fontWeight: FontWeight.w800),
                          ),
                          Text(
                            Format.orderStatusLabel(order.status),
                            style: const TextStyle(color: AppColors.muted, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
          ],
        ),
      ),
    );
  }
}
