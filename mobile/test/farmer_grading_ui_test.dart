import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/features/grading_forecast/models/grading_forecast_result.dart';
import 'package:pepper_care/features/grading_forecast/screens/berry_quality_result_screen.dart';
import 'package:pepper_care/features/grading_forecast/screens/price_forecast_screen.dart';
import 'package:pepper_care/l10n/app_localizations.dart';

final Uint8List _onePixelPng = base64Decode(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
);

Widget _app(Widget child) => MaterialApp(
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: child,
);

GradingForecastResult _result({
  String gradingStatus = 'ACCEPTED',
  String decision = 'GRADE_1',
  String? grade = 'V3 Grade 1',
  String qualityStatus = 'PASSED',
  String? rejectionReason,
  bool marketAvailable = true,
  String category = 'HIGH_UNCERTAINTY_OUTLOOK',
}) => GradingForecastResult.fromJson({
  'schema_version': 'phase6_decision_support_v1',
  'grading': {
    'status': gradingStatus,
    'decision': decision,
    'grade': grade,
    'model_confidence': marketAvailable ? 0.92 : 0.70,
    'quality_status': qualityStatus,
    'rejection_reason': rejectionReason,
    'confidence_interpretation': 'model score; not a calibrated probability',
  },
  'market': marketAvailable
      ? {
          'status': 'AVAILABLE',
          'source': 'EAC farm-gate reference price',
          'price_grade': 'Grade 1',
          'latest_reference_date': '2026-09-15',
          'latest_reference_price': 1987.5,
          'forecast_target_date': '2026-09-29',
          'forecast_return': 0.0015,
          'forecast_price': 1990.6,
          'forecast_direction': 'UP',
          'forecast_signal': 'HIGH_UNCERTAINTY',
          'model_vs_persistence': 'RIDGE_BETTER',
          'forecast_interval': {
            'lower': 1942.49,
            'upper': 2038.70,
            'label': 'validation-derived forecast interval',
          },
        }
      : {'status': 'NOT_AVAILABLE_UNCERTAIN_GRADE'},
  'decision_support': {
    'category': category,
    'summary': 'technical server summary',
    'limitations': ['technical server limitation'],
  },
  'trace': {
    'grading_model_sha256': 'abc',
    'forecast_model_specification': 'ridge',
  },
  'runtime': {
    'grading': 'ONNX_RUNTIME_CPU',
    'price': 'FROZEN_RECORDS',
    'mobile': 'BACKEND_API',
    'tflite': 'NOT_USED',
  },
});

void main() {
  testWidgets('accepted result leads with farmer grade and hides internals', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(800, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final result = _result();
    await tester.pumpWidget(
      _app(BerryQualityResultScreen(imageBytes: _onePixelPng, result: result)),
    );
    await tester.pumpAndSettle();

    expect(find.text('Berry Grade 1'), findsOneWidget);
    expect(find.text('View price outlook'), findsOneWidget);
    expect(find.text('Model score'), findsNothing);
    expect(find.text('Quality gate'), findsNothing);
    expect(find.textContaining('V3'), findsNothing);
    expect(find.textContaining('technical server'), findsNothing);
  });

  testWidgets('uncertain result explains retake and blocks price UI', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(800, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final result = _result(
      gradingStatus: 'UNCERTAIN',
      decision: 'UNCERTAIN_GRADE',
      grade: null,
      rejectionReason: 'grade_margin_below_minimum',
      marketAvailable: false,
      category: 'UNCERTAIN_GRADE',
    );
    await tester.pumpWidget(
      _app(BerryQualityResultScreen(imageBytes: _onePixelPng, result: result)),
    );
    await tester.pumpAndSettle();

    expect(
      find.text('We could not confidently assess this sample'),
      findsOneWidget,
    );
    expect(find.text('View price outlook'), findsNothing);
    expect(find.text('Check another sample'), findsOneWidget);
    expect(find.text('UNCERTAIN GRADE'), findsNothing);
  });

  testWidgets('price outlook emphasizes one price and hides research fields', (
    tester,
  ) async {
    final result = _result();
    await tester.pumpWidget(_app(PriceForecastScreen(result: result)));
    await tester.pumpAndSettle();

    expect(find.text('LKR 1990.60 / kg'), findsOneWidget);
    expect(find.text('Expected to rise'), findsOneWidget);
    expect(find.text('LKR 1987.50 / kg'), findsOneWidget);
    expect(find.text('Research trace'), findsNothing);
    expect(find.text('Persistence comparison'), findsNothing);
    expect(find.text('Validation-derived forecast interval'), findsNothing);
    expect(find.textContaining('RIDGE'), findsNothing);
    expect(find.textContaining('1942.49'), findsNothing);
  });
}
