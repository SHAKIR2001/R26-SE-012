import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/core/locale/app_locale.dart';
import 'package:pepper_care/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    await loadSavedLocale();
  });

  testWidgets('first launch asks for language before showing home', (
    WidgetTester tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(800, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();

    expect(find.textContaining('Choose your language'), findsOneWidget);

    await tester.tap(find.text('English'));
    await tester.pumpAndSettle();

    expect(find.text('Pepper Care'), findsOneWidget);
    expect(find.text('Quality &\nPrice'), findsOneWidget);
  });
}
