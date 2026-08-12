import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../navigation.dart';
import '../widgets/luxury_buttons.dart';
import '../widgets/water_logo.dart';
import 'otp_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phoneController = TextEditingController();
  final _nameController = TextEditingController();
  String? _fieldError;

  @override
  void dispose() {
    _phoneController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  bool get _phoneValid {
    final digits = _phoneController.text.replaceAll(RegExp(r'\D'), '');
    return digits.length >= 9 && digits.length <= 15;
  }

  Future<void> _sendOtp() async {
    setState(() => _fieldError = null);
    final phone = _phoneController.text.trim();
    if (!_phoneValid) {
      setState(() => _fieldError = 'Enter a valid phone number (e.g. 09 123456789).');
      return;
    }
    final auth = context.read<AuthProvider>();
    final name = _nameController.text.trim();
    final success = await auth.requestOtp(phone, fullName: name.isEmpty ? null : name);
    if (!mounted) return;
    if (success) {
      pushAndReplaceStack(context, OtpScreen(phone: phone));
    } else {
      _showError(auth.error ?? 'Failed to send the verification code.');
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final loading = auth.isLoading;

    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.brandGradient),
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight - 48),
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 460),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const WaterLogo(size: 92),
                          const SizedBox(height: 36),
                          _GlassCard(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Welcome',
                                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                        color: AppColors.navy,
                                        fontWeight: FontWeight.w800,
                                      ),
                                ),
                                const SizedBox(height: 6),
                                const Text(
                                  'Sign in to order fresh purified water to your door.',
                                  style: TextStyle(color: AppColors.muted, fontSize: 14),
                                ),
                                const SizedBox(height: 24),
                                const Text(
                                  'FULL NAME (OPTIONAL)',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 1.1,
                                    color: AppColors.muted,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                TextField(
                                  controller: _nameController,
                                  textCapitalization: TextCapitalization.words,
                                  decoration: const InputDecoration(
                                    hintText: 'e.g. Aung Aung',
                                    prefixIcon: Icon(Icons.person_outline_rounded),
                                  ),
                                ),
                                const SizedBox(height: 16),
                                const Text(
                                  'PHONE NUMBER',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 1.1,
                                    color: AppColors.muted,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                TextField(
                                  controller: _phoneController,
                                  keyboardType: TextInputType.phone,
                                  inputFormatters: [
                                    FilteringTextInputFormatter.allow(RegExp(r'[0-9+\s]')),
                                  ],
                                  decoration: InputDecoration(
                                    hintText: 'e.g. 09 123 456 789',
                                    prefixIcon: const Icon(Icons.phone_outlined),
                                    errorText: _fieldError,
                                  ),
                                  onChanged: (_) {
                                    if (_fieldError != null) setState(() => _fieldError = null);
                                  },
                                  onSubmitted: (_) => _sendOtp(),
                                ),
                                const SizedBox(height: 24),
                                LuxuryButton(
                                  onPressed: loading ? null : _sendOtp,
                                  loading: loading,
                                  child: const Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Text('Continue'),
                                      SizedBox(width: 8),
                                      Icon(Icons.arrow_forward_rounded, size: 20),
                                    ],
                                  ),
                                ),
                                const SizedBox(height: 14),
                                const Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.verified_user_outlined, size: 14, color: AppColors.muted),
                                    SizedBox(width: 6),
                                    Flexible(
                                      child: Text(
                                        'We will send a 6-digit verification code via SMS.',
                                        style: TextStyle(color: AppColors.muted, fontSize: 12),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

/// Frosted-glass style card used over the gradient background.
class _GlassCard extends StatelessWidget {
  const _GlassCard({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.25),
            blurRadius: 40,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: child,
    );
  }
}
