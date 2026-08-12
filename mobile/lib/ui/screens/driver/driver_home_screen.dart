import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../core/theme/app_theme.dart';
import '../../../providers/auth_provider.dart';
import '../../../providers/driver_provider.dart';
import '../../widgets/luxury_buttons.dart';
import '../../widgets/status_chip.dart';
import 'delivery_list_screen.dart';
import 'earnings_screen.dart';

class DriverHomeScreen extends StatefulWidget {
  const DriverHomeScreen({super.key});

  @override
  State<DriverHomeScreen> createState() => _DriverHomeScreenState();
}

class _DriverHomeScreenState extends State<DriverHomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DriverProvider>().loadAssignedOrders();
    });
  }

  @override
  Widget build(BuildContext context) {
    final driver = context.watch<DriverProvider>();
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            _buildHeader(context, auth.user?.fullName ?? ''),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _OnlineToggleCard(
                    isOnline: driver.isOnline,
                    onChanged: (v) => driver.toggleOnline(),
                  ),
                  const SizedBox(height: 20),
                  const SectionHeader(title: 'Today\'s summary'),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _SummaryTile(
                          label: 'Active jobs',
                          value: '${driver.activeJobs}',
                          icon: Icons.local_shipping_rounded,
                          gradient: AppColors.brandGradient,
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: _SummaryTile(
                          label: 'Delivered',
                          value: '0',
                          icon: Icons.check_circle_outline_rounded,
                          gradient: AppColors.goldGradient,
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: _SummaryTile(
                          label: 'Empties',
                          value: '0',
                          icon: Icons.recycling_outlined,
                          gradient: AppColors.waterGradient,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  LuxuryButton(
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const DeliveryListScreen()),
                      );
                    },
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.route_rounded, size: 20),
                        SizedBox(width: 8),
                        Text('View delivery jobs'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  LuxuryOutlineButton(
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const EarningsScreen()),
                      );
                    },
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.savings_outlined, size: 20),
                        SizedBox(width: 8),
                        Text('Earnings & history'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, String name) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 26),
      decoration: const BoxDecoration(
        gradient: AppColors.brandGradient,
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(28)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.16),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.delivery_dining_rounded, color: Colors.white, size: 24),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Text(
                  'Driver Dashboard',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              IconButton(
                onPressed: () async => context.read<AuthProvider>().logout(),
                tooltip: 'Log out',
                icon: const Icon(Icons.logout_rounded, color: Colors.white),
              ),
            ],
          ),
          const SizedBox(height: 18),
          Text(
            name.isEmpty ? 'Hello, Driver' : 'Hello, $name',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Keep the community hydrated.',
            style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class _OnlineToggleCard extends StatelessWidget {
  const _OnlineToggleCard({required this.isOnline, required this.onChanged});

  final bool isOnline;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final online = isOnline;
    return Card(
      child: Container(
        decoration: BoxDecoration(
          gradient: online ? AppColors.brandGradient : null,
          borderRadius: BorderRadius.circular(20),
        ),
        padding: const EdgeInsets.all(18),
        child: Row(
          children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: online ? Colors.white.withOpacity(0.16) : AppColors.canvas,
                shape: BoxShape.circle,
              ),
              child: Icon(
                online ? Icons.bolt_rounded : Icons.power_settings_new_rounded,
                color: online ? const Color(0xFFF3E5B5) : AppColors.muted,
                size: 24,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    online ? 'You are online' : 'You are offline',
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w800,
                      color: online ? Colors.white : AppColors.ink,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    online ? 'Accepting delivery requests' : 'Shift not started',
                    style: TextStyle(
                      fontSize: 12.5,
                      color: online ? Colors.white70 : AppColors.muted,
                    ),
                  ),
                ],
              ),
            ),
            Switch(
              value: online,
              onChanged: onChanged,
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryTile extends StatelessWidget {
  const _SummaryTile({
    required this.label,
    required this.value,
    required this.icon,
    required this.gradient,
  });

  final String label;
  final String value;
  final IconData icon;
  final Gradient gradient;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Column(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                gradient: gradient,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: Colors.white, size: 20),
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppColors.muted, fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}
