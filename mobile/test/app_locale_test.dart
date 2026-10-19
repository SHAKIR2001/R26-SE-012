import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/core/locale/app_locale.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    await loadSavedLocale();
  });

  test('persists and restores a supported locale', () async {
    await setLocale(const Locale('si'));

    expect(hasChosenLanguage, isTrue);
    expect(appLocale.value?.languageCode, 'si');
    expect(currentPromptLanguage(), 'Sinhala');

    appLocale.value = null;
    await loadSavedLocale();
    expect(appLocale.value?.languageCode, 'si');
  });

  test('ignores an unsupported stored locale', () async {
    SharedPreferences.setMockInitialValues({
      'app_locale_chosen': true,
      'app_locale_code': 'fr',
    });
    appLocale.value = null;

    await loadSavedLocale();

    expect(appLocale.value, isNull);
    expect(currentPromptLanguage(), 'English');
  });
}
