import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive/hive.dart';

const String themeSettingsBoxName = 'settings_box';
const String themeModeKey = 'theme_mode';

class ThemeModeNotifier extends StateNotifier<ThemeMode> {
  ThemeModeNotifier() : super(_loadInitial());

  static ThemeMode _loadInitial() {
    try {
      if (Hive.isBoxOpen(themeSettingsBoxName)) {
        final box = Hive.box<String>(themeSettingsBoxName);
        final saved = box.get(themeModeKey);
        if (saved == 'dark') return ThemeMode.dark;
        if (saved == 'light') return ThemeMode.light;
      }
    } catch (_) {}
    return ThemeMode.system;
  }

  void setThemeMode(ThemeMode mode) {
    state = mode;
    _save(mode);
  }

  void toggleTheme(BuildContext context) {
    final currentIsDark = state == ThemeMode.dark ||
        (state == ThemeMode.system &&
            MediaQuery.platformBrightnessOf(context) == Brightness.dark);
    final next = currentIsDark ? ThemeMode.light : ThemeMode.dark;
    setThemeMode(next);
  }

  Future<void> _save(ThemeMode mode) async {
    try {
      Box<String> box;
      if (Hive.isBoxOpen(themeSettingsBoxName)) {
        box = Hive.box<String>(themeSettingsBoxName);
      } else {
        box = await Hive.openBox<String>(themeSettingsBoxName);
      }
      final str = mode == ThemeMode.dark
          ? 'dark'
          : mode == ThemeMode.light
              ? 'light'
              : 'system';
      await box.put(themeModeKey, str);
    } catch (_) {}
  }
}

final themeModeProvider =
    StateNotifierProvider<ThemeModeNotifier, ThemeMode>((ref) {
  return ThemeModeNotifier();
});

/// Shared Theme Toggle Button Widget
class ThemeToggleButton extends ConsumerWidget {
  const ThemeToggleButton({super.key, this.iconColor = Colors.white});

  final Color iconColor;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mode = ref.watch(themeModeProvider);
    final isDark = mode == ThemeMode.dark ||
        (mode == ThemeMode.system &&
            MediaQuery.platformBrightnessOf(context) == Brightness.dark);
    final tooltip = isDark ? 'Switch to light mode' : 'Switch to dark mode';

    return Semantics(
      label: tooltip,
      button: true,
      child: IconButton(
        icon: Icon(
          isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
          color: iconColor,
        ),
        tooltip: tooltip,
        onPressed: () {
          ref.read(themeModeProvider.notifier).toggleTheme(context);
        },
      ),
    );
  }
}
