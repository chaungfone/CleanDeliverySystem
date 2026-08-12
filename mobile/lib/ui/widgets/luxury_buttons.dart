import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Primary CTA with the brand's navyâ†’blue gradient.
class LuxuryButton extends StatelessWidget {
  const LuxuryButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.loading = false,
    this.gradient = AppColors.brandGradient,
    this.width,
    this.height = 54,
    this.enabled = true,
  });

  final VoidCallback? onPressed;
  final Widget child;
  final bool loading;
  final Gradient gradient;
  final double? width;
  final double height;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final isEnabled = enabled && !loading && onPressed != null;
    return Opacity(
      opacity: isEnabled ? 1 : 0.45,
      child: SizedBox(
        width: width,
        height: height,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: gradient,
            borderRadius: BorderRadius.circular(16),
            boxShadow: isEnabled
                ? [
                    BoxShadow(
                      color: AppColors.navy.withOpacity(0.28),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ]
                : const [],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: isEnabled ? onPressed : null,
              borderRadius: BorderRadius.circular(16),
              child: Center(
                child: loading
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.4,
                          color: Colors.white,
                        ),
                      )
                    : child,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Secondary CTA: outlined with navy text.
class LuxuryOutlineButton extends StatelessWidget {
  const LuxuryOutlineButton({
    super.key,
    required this.onPressed,
    required this.child,
    this.height = 54,
    this.loading = false,
  });

  final VoidCallback? onPressed;
  final Widget child;
  final double height;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
      child: OutlinedButton(
        onPressed: loading ? null : onPressed,
        child: loading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2.2),
              )
            : child,
      ),
    );
  }
}
