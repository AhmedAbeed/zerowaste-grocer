import 'package:flutter/material.dart';

/// ZeroWaste Grocer brand color palette and theme contrast system.
abstract final class AppColors {
  // Brand & Eco Primary/Secondary
  static const Color forestGreen = Color(0xFF1B5E20);
  static const Color forestGreenDark = Color(0xFF81C784);
  static const Color mint = Color(0xFF2E7D32);

  // Light Mode Palette
  static const Color background = Color(0xFFF7FBF7);
  static const Color surface = Colors.white;
  static const Color surfaceVariant = Color(0xFFE8F5E9);
  static const Color text = Color(0xFF212121);
  static const Color textSecondary = Color(0xFF757575);
  static const Color divider = Color(0xFFE0E0E0);
  static const Color cardBorder = Color(0xFFE8E8E8);

  // Dark Mode Palette
  static const Color darkBackground = Color(0xFF0F1711);
  static const Color darkSurface = Color(0xFF18221B);
  static const Color darkSurfaceVariant = Color(0xFF243B28);
  static const Color darkText = Color(0xFFF1F5F2);
  static const Color darkTextSecondary = Color(0xFFA0B0A4);
  static const Color darkDivider = Color(0xFF2D3D30);
  static const Color darkCardBorder = Color(0xFF2C3A2F);

  // Status Colors Light
  static const Color critical = Color(0xFFD32F2F);
  static const Color warning = Color(0xFFBF360C);
  static const Color safe = Color(0xFF2E7D32);

  // Status Colors Dark (accessible contrast > 4.5:1)
  static const Color darkCritical = Color(0xFFEF5350);
  static const Color darkWarning = Color(0xFFFFB74D);
  static const Color darkSafe = Color(0xFF81C784);

  // Category Colors
  static const Color catProduce = Color(0xFF81C784);
  static const Color catDairy = Color(0xFF4FC3F7);
  static const Color catBakery = Color(0xFFFFB74D);
  static const Color catMeat = Color(0xFFF06292);
}

/// Extension providing theme-reactive colors directly on BuildContext
extension ThemeColors on BuildContext {
  bool get isDarkMode => Theme.of(this).brightness == Brightness.dark;
  Color get surfaceColor => Theme.of(this).cardColor;
  Color get scaffoldBg => Theme.of(this).scaffoldBackgroundColor;
  Color get textColor => isDarkMode ? AppColors.darkText : AppColors.text;
  Color get textSecondaryColor => isDarkMode ? AppColors.darkTextSecondary : AppColors.textSecondary;
  Color get cardBorderColor => isDarkMode ? AppColors.darkCardBorder : AppColors.cardBorder;
  Color get dividerColor => isDarkMode ? AppColors.darkDivider : AppColors.divider;
  Color get criticalColor => isDarkMode ? AppColors.darkCritical : AppColors.critical;
  Color get warningColor => isDarkMode ? AppColors.darkWarning : AppColors.warning;
  Color get safeColor => isDarkMode ? AppColors.darkSafe : AppColors.safe;
  Color get primaryBrand => isDarkMode ? AppColors.forestGreenDark : AppColors.forestGreen;
}
