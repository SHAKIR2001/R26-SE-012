import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'core/locale/app_locale.dart';
import 'core/theme/app_theme.dart';
import 'features/home/screens/home_screen.dart';
import 'features/history/data/history_repository.dart';
import 'features/history/history_scope.dart';
import 'features/onboarding/language_picker_screen.dart';
import 'l10n/app_localizations.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await loadSavedLocale();
  HistoryRepository? historyRepository;
  if (!kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS ||
          defaultTargetPlatform == TargetPlatform.macOS)) {
    try {
      historyRepository = await HistoryRepository.openDefault();
      await historyRepository.runMaintenance();
    } catch (error, stackTrace) {
      debugPrint('History storage unavailable: $error\n$stackTrace');
    }
  }
  runApp(MyApp(historyRepository: historyRepository));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key, this.historyRepository});

  final HistoryRepository? historyRepository;

  @override
  Widget build(BuildContext context) {
    final app = ValueListenableBuilder<ThemeMode>(
      valueListenable: appThemeMode,
      builder: (_, mode, __) => ValueListenableBuilder<Locale?>(
        valueListenable: appLocale,
        builder: (_, locale, __) => MaterialApp(
          title: 'Pepper Care',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light,
          darkTheme: AppTheme.dark,
          themeMode: mode,
          locale: locale,
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: hasChosenLanguage
              ? const HomeScreen()
              : const LanguagePickerScreen(),
        ),
      ),
    );
    final repository = historyRepository;
    return repository == null
        ? app
        : HistoryScope(repository: repository, child: app);
  }
}
