import 'package:flutter/material.dart';

/// Luxury water-delivery palette: deep navy + champagne gold + fresh water cyan.
class AppColors {
  AppColors._();

  static const Color navy = Color(0xFF0A2540); // deep navy — primary
  static const Color navySoft = Color(0xFF12365E);
  static const Color royal = Color(0xFF1D4ED8);
  static const Color blue = Color(0xFF1976D2); // brand blue (design system)
  static const Color teal = Color(0xFF009688); // secondary (design system)
  static const Color water = Color(0xFF38BDF8); // water cyan accent
  static const Color gold = Color(0xFFC9A227); // luxury gold
  static const Color champagne = Color(0xFFF3E5B5); // light gold tint
  static const Color ink = Color(0xFF14202E); // primary text
  static const Color muted = Color(0xFF64748B); // secondary text
  static const Color line = Color(0xFFE3E9F0); // borders
  static const Color canvas = Color(0xFFF5F7FB); // background
  static const Color success = Color(0xFF16A34A);
  static const Color warning = Color(0xFFD97706);
  static const Color danger = Color(0xFFDC2626);

  static const LinearGradient brandGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [navy, Color(0xFF0E3E6E), royal],
  );

  static const LinearGradient goldGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFE3C75E), gold, Color(0xFFA87F1F)],
  );

  static const LinearGradient waterGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [water, Color(0xFF0E7490)],
  );
}

/// Global theme for the app — Material 3 with a luxury look.
class AppTheme {
  AppTheme._();

  /// Fallback font so Myanmar text always renders (Pyidaungsu bundled).
  static const List<String> _myanmarFallback = ['Pyidaungsu'];

  static ThemeData light() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: const ColorScheme.light(
        primary: AppColors.navy,
        onPrimary: Colors.white,
        secondary: AppColors.teal,
        onSecondary: Colors.white,
        surface: Colors.white,
        onSurface: AppColors.ink,
        error: AppColors.danger,
        onError: Colors.white,
        outline: AppColors.line,
      ),
      scaffoldBackgroundColor: AppColors.canvas,
    );

    return base.copyWith(
      textTheme: _textTheme(base.textTheme),
      appBarTheme: AppBarTheme(
        elevation: 0,
        centerTitle: false,
        backgroundColor: AppColors.canvas,
        foregroundColor: AppColors.ink,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: _fb(base.textTheme.titleLarge?.copyWith(
          color: AppColors.ink,
          fontWeight: FontWeight.w700,
        )),
      ),
      cardTheme: CardTheme(
        elevation: 0,
        color: Colors.white,
        surfaceTintColor: Colors.transparent,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: AppColors.line),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.navy,
          foregroundColor: Colors.white,
          elevation: 0,
          minimumSize: const Size.fromHeight(54),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.navy,
          foregroundColor: Colors.white,
          elevation: 0,
          minimumSize: const Size.fromHeight(54),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.royal,
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.navy,
          minimumSize: const Size.fromHeight(54),
          side: const BorderSide(color: AppColors.line),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        hintStyle: const TextStyle(color: AppColors.muted),
        labelStyle: const TextStyle(color: AppColors.muted),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.royal, width: 1.6),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.danger),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.danger, width: 1.6),
        ),
      ),
      dividerTheme: const DividerThemeData(color: AppColors.line, thickness: 1),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.ink,
        contentTextStyle: const TextStyle(color: Colors.white),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: AppColors.royal,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: MaterialStateProperty.resolveWith(
          (states) => states.contains(MaterialState.selected) ? Colors.white : AppColors.muted,
        ),
        trackColor: MaterialStateProperty.resolveWith(
          (states) => states.contains(MaterialState.selected)
              ? AppColors.teal
              : AppColors.line,
        ),
      ),
      chipTheme: base.chipTheme.copyWith(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        side: const BorderSide(color: AppColors.line),
      ),
    );
  }

  static ThemeData dark() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.water,
        onPrimary: Color(0xFF04202F),
        secondary: AppColors.teal,
        onSecondary: Colors.white,
        surface: Color(0xFF101B2C),
        onSurface: Color(0xFFE6EDF7),
        error: Color(0xFFF87171),
        onError: Color(0xFF3B0A0A),
      ),
      scaffoldBackgroundColor: const Color(0xFF0A1424),
    );

    return base.copyWith(
      textTheme: _textTheme(base.textTheme),
      appBarTheme: AppBarTheme(
        elevation: 0,
        centerTitle: false,
        backgroundColor: const Color(0xFF0A1424),
        foregroundColor: const Color(0xFFE6EDF7),
        surfaceTintColor: Colors.transparent,
        titleTextStyle: _fb(base.textTheme.titleLarge?.copyWith(
          color: const Color(0xFFE6EDF7),
          fontWeight: FontWeight.w700,
        )),
      ),
      cardTheme: CardTheme(
        elevation: 0,
        color: const Color(0xFF14233B),
        surfaceTintColor: Colors.transparent,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: Color(0xFF23344F)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF14233B),
        hintStyle: const TextStyle(color: Color(0xFF8A9BB5)),
        labelStyle: const TextStyle(color: Color(0xFF8A9BB5)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF23344F)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF23344F)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: AppColors.water, width: 1.6),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }

  static ThemeData build({required Brightness brightness}) =>
      brightness == Brightness.dark ? dark() : light();

  /// Applies the Myanmar fallback font family to a style.
  static TextStyle? _fb(TextStyle? style) =>
      style?.copyWith(fontFamilyFallback: _myanmarFallback);

  static TextTheme _textTheme(TextTheme base) {
    return TextTheme(
      displayLarge: _withFb(base.displayLarge?.copyWith(fontSize: 40, fontWeight: FontWeight.w800, letterSpacing: -1)),
      displayMedium: _withFb(base.displayMedium?.copyWith(fontSize: 34, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
      displaySmall: _withFb(base.displaySmall?.copyWith(fontSize: 28, fontWeight: FontWeight.w800)),
      headlineLarge: _withFb(base.headlineLarge?.copyWith(fontSize: 26, fontWeight: FontWeight.w800)),
      headlineMedium: _withFb(base.headlineMedium?.copyWith(fontSize: 22, fontWeight: FontWeight.w700)),
      headlineSmall: _withFb(base.headlineSmall?.copyWith(fontSize: 20, fontWeight: FontWeight.w700)),
      titleLarge: _withFb(base.titleLarge?.copyWith(fontSize: 19, fontWeight: FontWeight.w700)),
      titleMedium: _withFb(base.titleMedium?.copyWith(fontSize: 16, fontWeight: FontWeight.w700)),
      titleSmall: _withFb(base.titleSmall?.copyWith(fontSize: 14, fontWeight: FontWeight.w600)),
      bodyLarge: _withFb(base.bodyLarge?.copyWith(fontSize: 16, height: 1.5)),
      bodyMedium: _withFb(base.bodyMedium?.copyWith(fontSize: 14, height: 1.45)),
      bodySmall: _withFb(base.bodySmall?.copyWith(fontSize: 12, height: 1.4, color: AppColors.muted)),
      labelLarge: _withFb(base.labelLarge?.copyWith(fontSize: 15, fontWeight: FontWeight.w600)),
      labelMedium: _withFb(base.labelMedium?.copyWith(fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.3)),
      labelSmall: _withFb(base.labelSmall?.copyWith(fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.4)),
    );
  }

  static TextStyle? _withFb(TextStyle? style) =>
      style?.copyWith(fontFamilyFallback: _myanmarFallback);
}
