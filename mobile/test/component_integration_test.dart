import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/features/berry_disease/berry_scanner_screen.dart';
import 'package:pepper_care/features/grading_forecast/screens/berry_capture_screen.dart';
import 'package:pepper_care/features/home/screens/home_screen.dart';
import 'package:pepper_care/features/plant_health/screens/plant_health_scanner_screen.dart';
import 'package:pepper_care/l10n/app_localizations.dart';
import 'package:pepper_care/shared/widgets/scanner_view.dart';

Widget _app() => const MaterialApp(
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: HomeScreen(),
);

void main() {
  Future<void> usePhoneViewport(WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(800, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
  }

  testWidgets('current shell retains the combined imported plant entry', (
    tester,
  ) async {
    await usePhoneViewport(tester);
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();

    for (final label in const [
      'Leaf & Pest',
      'Berry Disease',
      'Quality &\nPrice',
    ]) {
      expect(find.text(label), findsOneWidget);
    }
  });

  testWidgets(
    'grading entry uses the shared sheet then current capture route',
    (tester) async {
      await usePhoneViewport(tester);
      await tester.pumpWidget(_app());
      await tester.pumpAndSettle();

      final card = find.ancestor(
        of: find.text('Quality &\nPrice'),
        matching: find.byType(InkWell),
      );
      await tester.ensureVisible(card);
      await tester.tap(card);
      await tester.pumpAndSettle();

      expect(find.text('Berry Quality and Price Outlook'), findsOneWidget);
      await tester.tap(find.text('Check Berry Quality'));
      await tester.pumpAndSettle();

      expect(find.byType(BerryCaptureScreen), findsOneWidget);
      expect(find.textContaining('Grade 3'), findsNothing);
    },
  );

  testWidgets('combined plant entry loads leaf and pest local fallbacks', (
    tester,
  ) async {
    await usePhoneViewport(tester);
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();

    final plant = find.ancestor(
      of: find.text('Leaf & Pest'),
      matching: find.byType(InkWell),
    );
    await tester.ensureVisible(plant);
    await tester.tap(plant);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Start scan'));
    // Scanner camera/progress widgets may keep scheduling frames; pump only
    // through the route transition instead of waiting for global quiescence.
    await tester.pump(const Duration(milliseconds: 500));

    expect(
      find.byType(PlantHealthScannerScreen, skipOffstage: false),
      findsOneWidget,
    );
    final scanner = tester.widget<ScannerView>(
      find.byType(ScannerView, skipOffstage: false),
    );
    expect(
      scanner.modelConfig.assetPath,
      'assets/models/new_leaf_yolo_model_int8.tflite',
    );
    expect(scanner.additionalFallbackConfigs, hasLength(1));
    expect(
      scanner.additionalFallbackConfigs.single.assetPath,
      'assets/models/new_pest_yolo_model_int8.tflite',
    );
  });

  testWidgets('berry-disease entry reaches the imported berry scanner', (
    tester,
  ) async {
    await usePhoneViewport(tester);
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();

    final berries = find.ancestor(
      of: find.text('Berry Disease'),
      matching: find.byType(InkWell),
    );
    await tester.ensureVisible(berries);
    await tester.tap(berries);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Start scan'));
    await tester.pump(const Duration(milliseconds: 500));

    expect(
      find.byType(BerryScannerScreen, skipOffstage: false),
      findsOneWidget,
    );
  });
}
