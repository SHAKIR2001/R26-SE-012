import 'package:flutter/material.dart';

const Color kBrand = Color(0xFF1B5E3B);
const Color _brandDark = Color(0xFF78D5A1);
const Color _surfaceLight = Color(0xFFF6F8F5);
const Color _surfaceDark = Color(0xFF0F1713);
const Color kWarmAccent = Color(0xFF9A5500);

const List<String> _fontFallbacks = [
  'Noto Sans Sinhala',
  'Noto Sans Tamil',
  'Noto Sans',
  'sans-serif',
];

final ValueNotifier<ThemeMode> appThemeMode = ValueNotifier<ThemeMode>(
  ThemeMode.light,
);

bool get isDarkMode => appThemeMode.value == ThemeMode.dark;

void toggleTheme() {
  appThemeMode.value = isDarkMode ? ThemeMode.light : ThemeMode.dark;
}

@immutable
class AppStatusColors extends ThemeExtension<AppStatusColors> {
  const AppStatusColors({
    required this.success,
    required this.successContainer,
    required this.onSuccessContainer,
    required this.warning,
    required this.warningContainer,
    required this.onWarningContainer,
    required this.danger,
    required this.dangerContainer,
    required this.onDangerContainer,
    required this.info,
    required this.infoContainer,
    required this.onInfoContainer,
  });

  final Color success;
  final Color successContainer;
  final Color onSuccessContainer;
  final Color warning;
  final Color warningContainer;
  final Color onWarningContainer;
  final Color danger;
  final Color dangerContainer;
  final Color onDangerContainer;
  final Color info;
  final Color infoContainer;
  final Color onInfoContainer;

  static const light = AppStatusColors(
    success: Color(0xFF1F7543),
    successContainer: Color(0xFFD9F3E4),
    onSuccessContainer: Color(0xFF0B3B23),
    warning: Color(0xFF955100),
    warningContainer: Color(0xFFFFE2B8),
    onWarningContainer: Color(0xFF442500),
    danger: Color(0xFFB3261E),
    dangerContainer: Color(0xFFFFDAD6),
    onDangerContainer: Color(0xFF410002),
    info: Color(0xFF245EA8),
    infoContainer: Color(0xFFD8E7FF),
    onInfoContainer: Color(0xFF0B315F),
  );

  static const dark = AppStatusColors(
    success: Color(0xFF7DDEA5),
    successContainer: Color(0xFF173E29),
    onSuccessContainer: Color(0xFFD2F9DF),
    warning: Color(0xFFFFBF78),
    warningContainer: Color(0xFF4B2D0B),
    onWarningContainer: Color(0xFFFFE1BE),
    danger: Color(0xFFFFB4AB),
    dangerContainer: Color(0xFF5A1A17),
    onDangerContainer: Color(0xFFFFDAD6),
    info: Color(0xFFA8C7FA),
    infoContainer: Color(0xFF173A64),
    onInfoContainer: Color(0xFFD8E7FF),
  );

  static AppStatusColors of(BuildContext context) =>
      Theme.of(context).extension<AppStatusColors>() ??
      (Theme.of(context).brightness == Brightness.dark
          ? AppStatusColors.dark
          : AppStatusColors.light);

  @override
  AppStatusColors copyWith({
    Color? success,
    Color? successContainer,
    Color? onSuccessContainer,
    Color? warning,
    Color? warningContainer,
    Color? onWarningContainer,
    Color? danger,
    Color? dangerContainer,
    Color? onDangerContainer,
    Color? info,
    Color? infoContainer,
    Color? onInfoContainer,
  }) => AppStatusColors(
    success: success ?? this.success,
    successContainer: successContainer ?? this.successContainer,
    onSuccessContainer: onSuccessContainer ?? this.onSuccessContainer,
    warning: warning ?? this.warning,
    warningContainer: warningContainer ?? this.warningContainer,
    onWarningContainer: onWarningContainer ?? this.onWarningContainer,
    danger: danger ?? this.danger,
    dangerContainer: dangerContainer ?? this.dangerContainer,
    onDangerContainer: onDangerContainer ?? this.onDangerContainer,
    info: info ?? this.info,
    infoContainer: infoContainer ?? this.infoContainer,
    onInfoContainer: onInfoContainer ?? this.onInfoContainer,
  );

  @override
  AppStatusColors lerp(AppStatusColors? other, double t) {
    if (other == null) return this;
    return AppStatusColors(
      success: Color.lerp(success, other.success, t)!,
      successContainer: Color.lerp(
        successContainer,
        other.successContainer,
        t,
      )!,
      onSuccessContainer: Color.lerp(
        onSuccessContainer,
        other.onSuccessContainer,
        t,
      )!,
      warning: Color.lerp(warning, other.warning, t)!,
      warningContainer: Color.lerp(
        warningContainer,
        other.warningContainer,
        t,
      )!,
      onWarningContainer: Color.lerp(
        onWarningContainer,
        other.onWarningContainer,
        t,
      )!,
      danger: Color.lerp(danger, other.danger, t)!,
      dangerContainer: Color.lerp(dangerContainer, other.dangerContainer, t)!,
      onDangerContainer: Color.lerp(
        onDangerContainer,
        other.onDangerContainer,
        t,
      )!,
      info: Color.lerp(info, other.info, t)!,
      infoContainer: Color.lerp(infoContainer, other.infoContainer, t)!,
      onInfoContainer: Color.lerp(
        onInfoContainer,
        other.onInfoContainer,
        t,
      )!,
    );
  }
}

class AppTheme {
  const AppTheme._();

  static final ThemeData light = _buildTheme(
    brightness: Brightness.light,
    scheme: const ColorScheme.light(
      primary: kBrand,
      onPrimary: Colors.white,
      primaryContainer: Color(0xFFD9F2E3),
      onPrimaryContainer: Color(0xFF0B3D25),
      secondary: Color(0xFF805000),
      onSecondary: Colors.white,
      secondaryContainer: Color(0xFFFFE2B8),
      onSecondaryContainer: Color(0xFF442500),
      error: Color(0xFFB3261E),
      onError: Colors.white,
      errorContainer: Color(0xFFFFDAD6),
      onErrorContainer: Color(0xFF410002),
      surface: _surfaceLight,
      onSurface: Color(0xFF17201B),
      surfaceContainerLowest: Colors.white,
      surfaceContainerLow: Color(0xFFF0F4F1),
      surfaceContainer: Color(0xFFE9EFEB),
      surfaceContainerHigh: Color(0xFFDFE7E1),
      surfaceContainerHighest: Color(0xFFD5DED7),
      onSurfaceVariant: Color(0xFF45524A),
      outline: Color(0xFF68766E),
      outlineVariant: Color(0xFFC7D2CA),
    ),
    statusColors: AppStatusColors.light,
  );

  static final ThemeData dark = _buildTheme(
    brightness: Brightness.dark,
    scheme: const ColorScheme.dark(
      primary: _brandDark,
      onPrimary: Color(0xFF00391E),
      primaryContainer: Color(0xFF145B38),
      onPrimaryContainer: Color(0xFFC9F7DA),
      secondary: Color(0xFFFFBF78),
      onSecondary: Color(0xFF4A2800),
      secondaryContainer: Color(0xFF633B00),
      onSecondaryContainer: Color(0xFFFFDDB4),
      error: Color(0xFFFFB4AB),
      onError: Color(0xFF690005),
      errorContainer: Color(0xFF93000A),
      onErrorContainer: Color(0xFFFFDAD6),
      surface: _surfaceDark,
      onSurface: Color(0xFFE5EEE8),
      surfaceContainerLowest: Color(0xFF0A110D),
      surfaceContainerLow: Color(0xFF15201A),
      surfaceContainer: Color(0xFF1A2720),
      surfaceContainerHigh: Color(0xFF233129),
      surfaceContainerHighest: Color(0xFF2C3B32),
      onSurfaceVariant: Color(0xFFC3CEC6),
      outline: Color(0xFF91A097),
      outlineVariant: Color(0xFF3F4D45),
    ),
    statusColors: AppStatusColors.dark,
  );

  static ThemeData _buildTheme({
    required Brightness brightness,
    required ColorScheme scheme,
    required AppStatusColors statusColors,
  }) {
    final dark = brightness == Brightness.dark;
    final base = ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      fontFamily: 'Roboto',
      fontFamilyFallback: _fontFallbacks,
    );
    final textTheme = base.textTheme.copyWith(
      displaySmall: base.textTheme.displaySmall?.copyWith(
        fontSize: 38,
        height: 1.08,
        fontWeight: FontWeight.w800,
        letterSpacing: -0.6,
      ),
      headlineLarge: base.textTheme.headlineLarge?.copyWith(
        fontSize: 30,
        height: 1.16,
        fontWeight: FontWeight.w800,
      ),
      headlineMedium: base.textTheme.headlineMedium?.copyWith(
        fontSize: 27,
        height: 1.18,
        fontWeight: FontWeight.w800,
      ),
      headlineSmall: base.textTheme.headlineSmall?.copyWith(
        fontSize: 24,
        height: 1.2,
        fontWeight: FontWeight.w800,
      ),
      titleLarge: base.textTheme.titleLarge?.copyWith(
        fontSize: 21,
        height: 1.25,
        fontWeight: FontWeight.w700,
      ),
      titleMedium: base.textTheme.titleMedium?.copyWith(
        fontSize: 18,
        height: 1.3,
        fontWeight: FontWeight.w700,
      ),
      titleSmall: base.textTheme.titleSmall?.copyWith(
        fontSize: 16,
        height: 1.35,
        fontWeight: FontWeight.w700,
      ),
      bodyLarge: base.textTheme.bodyLarge?.copyWith(fontSize: 17, height: 1.5),
      bodyMedium: base.textTheme.bodyMedium?.copyWith(
        fontSize: 16,
        height: 1.48,
      ),
      bodySmall: base.textTheme.bodySmall?.copyWith(fontSize: 14, height: 1.45),
      labelLarge: base.textTheme.labelLarge?.copyWith(
        fontSize: 16,
        height: 1.25,
        fontWeight: FontWeight.w700,
      ),
      labelMedium: base.textTheme.labelMedium?.copyWith(
        fontSize: 14,
        height: 1.3,
        fontWeight: FontWeight.w700,
      ),
      labelSmall: base.textTheme.labelSmall?.copyWith(
        fontSize: 13,
        height: 1.3,
        fontWeight: FontWeight.w600,
      ),
    );

    return base.copyWith(
      textTheme: textTheme,
      scaffoldBackgroundColor: scheme.surface,
      extensions: [statusColors],
      iconTheme: IconThemeData(color: scheme.onSurfaceVariant, size: 24),
      appBarTheme: AppBarTheme(
        centerTitle: false,
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
        elevation: 0,
        scrolledUnderElevation: 0,
        iconTheme: IconThemeData(color: scheme.onSurface, size: 25),
        actionsIconTheme: IconThemeData(color: scheme.onSurface, size: 24),
        titleTextStyle: textTheme.titleLarge?.copyWith(
          color: scheme.onSurface,
          fontWeight: FontWeight.w800,
        ),
      ),
      cardTheme: CardThemeData(
        color: scheme.surfaceContainerLowest,
        elevation: 0,
        margin: EdgeInsets.zero,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(22),
          side: BorderSide(color: scheme.outlineVariant),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          disabledBackgroundColor: scheme.surfaceContainerHighest,
          disabledForegroundColor: scheme.onSurfaceVariant,
          minimumSize: const Size(48, 56),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          textStyle: textTheme.labelLarge,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          minimumSize: const Size(48, 56),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          textStyle: textTheme.labelLarge,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: scheme.primary,
          minimumSize: const Size(48, 54),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
          textStyle: textTheme.labelLarge,
          side: BorderSide(color: scheme.outline),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: scheme.primary,
          minimumSize: const Size(48, 48),
          textStyle: textTheme.labelLarge,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 76,
        elevation: 0,
        backgroundColor: dark
            ? scheme.surfaceContainerLow
            : scheme.surfaceContainerLowest,
        indicatorColor: scheme.primaryContainer,
        indicatorShape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        iconTheme: WidgetStateProperty.resolveWith(
          (states) => IconThemeData(
            size: 25,
            color: states.contains(WidgetState.selected)
                ? scheme.onPrimaryContainer
                : scheme.onSurfaceVariant,
          ),
        ),
        labelTextStyle: WidgetStateProperty.resolveWith(
          (states) => textTheme.labelMedium?.copyWith(
            fontSize: 13.5,
            color: states.contains(WidgetState.selected)
                ? scheme.onSurface
                : scheme.onSurfaceVariant,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w800
                : FontWeight.w600,
          ),
        ),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        showDragHandle: true,
        backgroundColor: scheme.surfaceContainerLow,
        modalBackgroundColor: scheme.surfaceContainerLow,
        surfaceTintColor: Colors.transparent,
        dragHandleColor: scheme.outline,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        ),
      ),
      dividerTheme: DividerThemeData(color: scheme.outlineVariant),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surfaceContainerLow,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 18,
          vertical: 16,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: dark
            ? scheme.surfaceContainerHighest
            : const Color(0xFF26332B),
        contentTextStyle: textTheme.bodyMedium?.copyWith(color: Colors.white),
        actionTextColor: dark ? scheme.primary : const Color(0xFFB7F0CC),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
