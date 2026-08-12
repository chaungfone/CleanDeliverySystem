import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// The app's logo mark: a water droplet on a brand gradient tile.
class WaterLogo extends StatelessWidget {
  const WaterLogo({super.key, this.size = 84, this.showLabel = true});

  final double size;
  final bool showLabel;

  @override
  Widget build(BuildContext context) {
    final icon = Icon(Icons.water_drop_rounded, color: Colors.white, size: size * 0.5);
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            gradient: AppColors.brandGradient,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: AppColors.navy.withOpacity(0.35),
                blurRadius: 24,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Center(child: icon),
        ),
        if (showLabel) ...[
          const SizedBox(height: 16),
          const Text(
            'Clean Delivery',
            style: TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.4,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Pure water, delivered fresh',
            style: TextStyle(
              color: Colors.white.withOpacity(0.75),
              fontSize: 13,
              letterSpacing: 0.6,
            ),
          ),
        ],
      ],
    );
  }
}

/// Small inline logo for app bars.
class CompactLogo extends StatelessWidget {
  const CompactLogo({super.key, this.dark = false});

  final bool dark;

  @override
  Widget build(BuildContext context) {
    final color = dark ? AppColors.navy : Colors.white;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            gradient: AppColors.brandGradient,
            borderRadius: BorderRadius.circular(11),
          ),
          child: const Icon(Icons.water_drop_rounded, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 10),
        Text(
          'Clean Delivery',
          style: TextStyle(
            color: color,
            fontSize: 17,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.2,
          ),
        ),
      ],
    );
  }
}
