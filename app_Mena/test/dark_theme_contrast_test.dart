// ignore_for_file: avoid_print, prefer_interpolation_to_compose_strings
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:zerowaste_grocer/core/theme/app_colors.dart';

double sRGBToLuminance(Color color) {
  double channel(int c) {
    final v = c / 255.0;
    return v <= 0.03928 ? v / 12.92 : math.pow((v + 0.055) / 1.055, 2.4).toDouble();
  }

  final r = (color.r * 255.0).round().clamp(0, 255);
  final g = (color.g * 255.0).round().clamp(0, 255);
  final b = (color.b * 255.0).round().clamp(0, 255);
  return 0.2126 * channel(r) +
      0.7152 * channel(g) +
      0.0722 * channel(b);
}

double contrastRatio(Color c1, Color c2) {
  final l1 = sRGBToLuminance(c1);
  final l2 = sRGBToLuminance(c2);
  final lighter = math.max(l1, l2);
  final darker = math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

void main() {
  test('WCAG 2.1 Contrast Ratios for Light and Dark themes', () {
    final checks = <({String name, Color fg, Color bg, double minRatio})>[
      // Dark Mode Text (>= 4.5:1)
      (
        name: 'Dark Primary Text on Surface',
        fg: AppColors.darkText,
        bg: AppColors.darkSurface,
        minRatio: 4.5,
      ),
      (
        name: 'Dark Secondary Text on Surface',
        fg: AppColors.darkTextSecondary,
        bg: AppColors.darkSurface,
        minRatio: 4.5,
      ),
      (
        name: 'Dark Primary Text on Background',
        fg: AppColors.darkText,
        bg: AppColors.darkBackground,
        minRatio: 4.5,
      ),
      (
        name: 'Dark Secondary Text on Background',
        fg: AppColors.darkTextSecondary,
        bg: AppColors.darkBackground,
        minRatio: 4.5,
      ),
      (
        name: 'Dark Critical Text on Surface',
        fg: AppColors.darkCritical,
        bg: AppColors.darkSurface,
        minRatio: 4.5,
      ),
      (
        name: 'Dark Warning Text on Surface',
        fg: AppColors.darkWarning,
        bg: AppColors.darkSurface,
        minRatio: 4.5,
      ),
      (
        name: 'Dark Safe Text on Surface',
        fg: AppColors.darkSafe,
        bg: AppColors.darkSurface,
        minRatio: 4.5,
      ),

      // Dark Mode Chart Graphical Elements (>= 3.0:1)
      (
        name: 'Dark Produce Chart Series vs Card Surface',
        fg: AppColors.catProduce,
        bg: AppColors.darkSurface,
        minRatio: 3.0,
      ),
      (
        name: 'Dark Dairy Chart Series vs Card Surface',
        fg: AppColors.catDairy,
        bg: AppColors.darkSurface,
        minRatio: 3.0,
      ),
      (
        name: 'Dark Bakery Chart Series vs Card Surface',
        fg: AppColors.catBakery,
        bg: AppColors.darkSurface,
        minRatio: 3.0,
      ),
      (
        name: 'Dark Meat Chart Series vs Card Surface',
        fg: AppColors.catMeat,
        bg: AppColors.darkSurface,
        minRatio: 3.0,
      ),

      // Light Mode Text (>= 4.5:1)
      (
        name: 'Light Primary Text on Surface',
        fg: AppColors.text,
        bg: AppColors.surface,
        minRatio: 4.5,
      ),
      (
        name: 'Light Secondary Text on Surface',
        fg: AppColors.textSecondary,
        bg: AppColors.surface,
        minRatio: 4.5,
      ),
      (
        name: 'Light Critical on Surface',
        fg: AppColors.critical,
        bg: AppColors.surface,
        minRatio: 4.5,
      ),
      (
        name: 'Light Warning on Surface',
        fg: AppColors.warning,
        bg: AppColors.surface,
        minRatio: 4.5,
      ),
      (
        name: 'Light Safe on Surface',
        fg: AppColors.safe,
        bg: AppColors.surface,
        minRatio: 4.5,
      ),

      // Light Mode Chart Graphical Elements (>= 3.0:1)
      (
        name: 'Light Produce Series vs Surface',
        fg: const Color(0xFF2E7D32),
        bg: AppColors.surface,
        minRatio: 3.0,
      ),
      (
        name: 'Light Dairy Series vs Surface',
        fg: const Color(0xFF0288D1),
        bg: AppColors.surface,
        minRatio: 3.0,
      ),
      (
        name: 'Light Bakery Series vs Surface',
        fg: const Color(0xFFE65100),
        bg: AppColors.surface,
        minRatio: 3.0,
      ),
      (
        name: 'Light Meat Series vs Surface',
        fg: const Color(0xFFC2185B),
        bg: AppColors.surface,
        minRatio: 3.0,
      ),
    ];

    print('\n' + '=' * 80);
    print('WCAG 2.1 CONTRAST RATIO TABLE');
    print('=' * 80);
    print(
      '${'Pair Name'.padRight(42)} | ${'Ratio'.padRight(8)} | ${'Min Req'.padRight(8)} | Verdict',
    );
    print('-' * 80);

    for (final check in checks) {
      final ratio = contrastRatio(check.fg, check.bg);
      final passed = ratio >= check.minRatio;
      print(
        '${check.name.padRight(42)} | ${ratio.toStringAsFixed(2).padRight(8)} | ${check.minRatio.toStringAsFixed(1).padRight(8)} | ${passed ? "PASS" : "FAIL"}',
      );
      expect(
        passed,
        isTrue,
        reason:
            '${check.name} failed WCAG contrast: $ratio < ${check.minRatio}',
      );
    }
    print('=' * 80);
  });
}
