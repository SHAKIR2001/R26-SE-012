import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Languages the app ships: English, Sinhala, Tamil.
const List<Locale> kSupportedLocales = [
  Locale('en'),
  Locale('si'),
  Locale('ta'),
];

/// Global locale. The root [MaterialApp] listens to this, so changing it
/// rebuilds the whole tree in the new language — same pattern as the theme
/// notifier. Null until the user has picked (the starter screen then shows).
final ValueNotifier<Locale?> appLocale = ValueNotifier<Locale?>(null);

const _kLocaleKey = 'app_locale_code';
const _kChosenKey = 'app_locale_chosen';

bool _chosen = false;

/// Whether the user has already picked a language (controls whether the app
/// opens on the starter language picker or straight into the home screen).
bool get hasChosenLanguage => _chosen;

/// Loads the saved language before the app builds. Safe if nothing is stored.
Future<void> loadSavedLocale() async {
  try {
    final prefs = await SharedPreferences.getInstance();
    _chosen = prefs.getBool(_kChosenKey) ?? false;
    final code = prefs.getString(_kLocaleKey);
    if (code != null && kSupportedLocales.any((l) => l.languageCode == code)) {
      appLocale.value = Locale(code);
    }
  } catch (_) {
    // First run / storage unavailable → fall through to the picker.
  }
}

/// Sets and persists the app language.
Future<void> setLocale(Locale locale) async {
  appLocale.value = locale;
  _chosen = true;
  try {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kLocaleKey, locale.languageCode);
    await prefs.setBool(_kChosenKey, true);
  } catch (_) {
    // Non-fatal: the choice still applies for this session.
  }
}

/// English name of the active language, for instructing the AI which language to
/// write its free-text answers in. Defaults to English.
String currentPromptLanguage() {
  switch (appLocale.value?.languageCode) {
    case 'si':
      return 'Sinhala';
    case 'ta':
      return 'Tamil';
    default:
      return 'English';
  }
}

/// Native display name for a supported language code.
String languageDisplayName(String code) {
  switch (code) {
    case 'si':
      return 'සිංහල';
    case 'ta':
      return 'தமிழ்';
    default:
      return 'English';
  }
}
