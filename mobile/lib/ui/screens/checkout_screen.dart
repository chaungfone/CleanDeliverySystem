import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/storage/token_storage.dart';
import '../../core/theme/app_theme.dart';
import '../../core/utils/formatters.dart';
import '../../data/models/order.dart';
import '../../providers/home_provider.dart';
import '../../providers/order_provider.dart';
import '../widgets/luxury_buttons.dart';
import '../widgets/status_chip.dart';
import 'tracking_screen.dart';

class CheckoutScreen extends StatefulWidget {
  const CheckoutScreen({super.key});

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  static const _methods = [
    ('COD', 'Cash on delivery', Icons.payments_outlined),
    ('KPAY', 'KBZ Pay', Icons.account_balance_wallet_outlined),
    ('WAVE_PAY', 'Wave Pay', Icons.phone_iphone_outlined),
  ];

  late final TextEditingController _addressController;
  String _method = 'COD';
  int _emptyBottles = 0;
  bool _loadingOrders = false;

  @override
  void initState() {
    super.initState();
    final storage = context.read<TokenStorage>();
    _addressController = TextEditingController(text: storage.lastAddressText ?? '');
    WidgetsBinding.instance.addPostFrameCallback((_) => _prefetchHistory());
  }

  Future<void> _prefetchHistory() async {
    final provider = context.read<OrderProvider>();
    if (provider.orders.isNotEmpty) return;
    setState(() => _loadingOrders = true);
    await provider.loadOrders(showLoading: false);
    if (mounted) setState(() => _loadingOrders = false);
  }

  @override
  void dispose() {
    _addressController.dispose();
    super.dispose();
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _placeOrder() async {
    final home = context.read<HomeProvider>();
    final orders = context.read<OrderProvider>();
    final storage = context.read<TokenStorage>();

    final addressId = orders.lastUsedAddressId;
    if (addressId == null) {
      _showError(
        'No registered delivery address found. Please place your first order from the website, or contact support.',
      );
      return;
    }

    final request = OrderCreateRequest(
      addressId: addressId,
      paymentMethod: _method,
      emptyBottlesReturned: _emptyBottles,
      items: [
        for (final product in home.cartProducts)
          OrderItemCreateRequest(
            productId: product.id,
            quantity: home.quantityOf(product.id),
          ),
      ],
    );

    await storage.saveAddressText(_addressController.text.trim());

    final success = await orders.placeOrder(request);
    if (!mounted) return;
    if (success) {
      final placed = orders.lastPlacedOrder;
      home.clearCart();
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => TrackingScreen(orderId: placed?.id ?? ''),
        ),
      );
    } else {
      _showError(orders.error ?? 'Failed to place the order. Please try again.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final home = context.watch<HomeProvider>();
    final orders = context.watch<OrderProvider>();
    final items = home.cartProducts;
    final addressId = orders.lastUsedAddressId;
    final loading = orders.isLoading;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Checkout'),
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.arrow_back_rounded),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            const SectionHeader(title: 'Your order'),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    for (final product in items) ...[
                      _OrderLine(
                        name: product.name,
                        quantity: home.quantityOf(product.id),
                        unitPrice: product.price,
                      ),
                      if (product != items.last) const Divider(height: 16),
                    ],
                    const Divider(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Subtotal', style: Theme.of(context).textTheme.bodyMedium),
                        Text(
                          Format.money(home.cartTotal),
                          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            if (items.isEmpty) ...[
              const SizedBox(height: 12),
              const Text(
                'Your cart is empty.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.muted),
              ),
            ],

            const SizedBox(height: 24),
            const SectionHeader(title: 'Delivery address'),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    TextField(
                      controller: _addressController,
                      maxLines: 2,
                      decoration: const InputDecoration(
                        hintText: 'Street address, ward/township, city',
                        prefixIcon: Icon(Icons.location_on_outlined),
                      ),
                    ),
                    const SizedBox(height: 10),
                    if (addressId != null)
                      const Row(
                        children: [
                          Icon(Icons.check_circle_outline, size: 16, color: AppColors.success),
                          SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              'We will deliver to your registered address on file.',
                              style: TextStyle(color: AppColors.success, fontSize: 12),
                            ),
                          ),
                        ],
                      )
                    else if (_loadingOrders)
                      const Text(
                        'Checking your registered addressâ€¦',
                        style: TextStyle(color: AppColors.muted, fontSize: 12),
                      )
                    else
                      const Text(
                        'No registered address found yet â€” please contact support to set one up.',
                        style: TextStyle(color: AppColors.warning, fontSize: 12),
                      ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),
            const SectionHeader(title: 'Payment method'),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  children: [
                    for (final (value, label, icon) in _methods)
                      RadioListTile<String>(
                        value: value,
                        groupValue: _method,
                        onChanged: (v) => setState(() => _method = v ?? 'COD'),
                        activeColor: AppColors.navy,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        title: Text(label),
                        secondary: Icon(icon, color: AppColors.navy),
                      ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),
            const SectionHeader(title: 'Empty bottles to return'),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const Icon(Icons.recycling_outlined, color: AppColors.teal),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Empty bottles', style: TextStyle(fontWeight: FontWeight.w700)),
                          Text(
                            'We will collect them and deduct the deposit.',
                            style: TextStyle(color: AppColors.muted, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    IconButton.outlined(
                      onPressed: () {
                        if (_emptyBottles > 0) setState(() => _emptyBottles--);
                      },
                      icon: const Icon(Icons.remove_rounded),
                    ),
                    SizedBox(
                      width: 40,
                      child: Text(
                        '$_emptyBottles',
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                      ),
                    ),
                    IconButton.outlined(
                      onPressed: () => setState(() => _emptyBottles++),
                      icon: const Icon(Icons.add_rounded),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 28),
            LuxuryButton(
              onPressed: loading ? null : _placeOrder,
              loading: loading,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('Confirm order'),
                  const SizedBox(width: 8),
                  Text(
                    'Â· ${Format.money(home.cartTotal)}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.lock_outline, size: 13, color: AppColors.muted),
                SizedBox(width: 6),
                Text(
                  'Your payment details are safe and encrypted.',
                  style: TextStyle(color: AppColors.muted, fontSize: 12),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _OrderLine extends StatelessWidget {
  const _OrderLine({
    required this.name,
    required this.quantity,
    required this.unitPrice,
  });

  final String name;
  final int quantity;
  final double unitPrice;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: AppColors.canvas,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            '$quantityÃ—',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.navy),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(name, maxLines: 1, overflow: TextOverflow.ellipsis),
        ),
        Text(Format.money(unitPrice * quantity)),
      ],
    );
  }
}
