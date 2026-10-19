import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/features/recommendations/ai_pest_service.dart';
import 'package:pepper_care/features/recommendations/pest_analysis.dart';
import 'package:pepper_care/features/recommendations/pest_analysis_screen.dart';
import 'package:pepper_care/features/recommendations/pest_treatment_engine.dart';
import 'package:pepper_care/features/recommendations/remediation_engine.dart';
import 'package:pepper_care/l10n/app_localizations.dart';
import 'package:pepper_care/shared/models/detection.dart';
import 'package:pepper_care/shared/widgets/scanner_view.dart';

const _pterolopha = Detection(
  classId: 2,
  className: 'Pterolopha annulata',
  score: 0.91,
  rect: Rect.fromLTWH(0.1, 0.1, 0.4, 0.4),
  color: Colors.purple,
);

Map<String, dynamic> _analysisJson({
  bool isPepperPlant = true,
  bool healthy = false,
  String pestType = 'Gynaikothrips karny',
}) => {
  'is_pepper_plant': isPepperPlant,
  'healthy': healthy,
  'pest_type': pestType,
  'plant_part': 'leaf',
  'pest_count': 1,
  'severity_percentage': 30,
  'confidence': 0.8,
  'affected_regions': 'Folded leaf',
  'summary': 'Visible pest damage.',
};

void main() {
  test('normal-confidence pest detection is passed to recommendations', () {
    expect(
      detectedPestForRecommendations(_pterolopha, lowConfidence: false),
      'Pterolopha annulata',
    );
  });

  test('relaxed pest detection is not treated as a confirmed species', () {
    expect(
      detectedPestForRecommendations(_pterolopha, lowConfidence: true),
      isNull,
    );
  });

  test('detail analysis cannot replace an anchored pest species', () {
    final reconciled = AiPestService.applyKnownPest(
      _analysisJson(),
      'Pterolopha annulata',
    );

    expect(reconciled['pest_type'], 'Pterolopha annulata');
    expect(reconciled['healthy'], isFalse);
  });

  test('conflicting healthy detail result becomes uncertain', () {
    final reconciled = AiPestService.applyKnownPest(
      _analysisJson(healthy: true, pestType: 'Healthy'),
      'Pterolopha annulata',
    );

    expect(reconciled['pest_type'], 'Uncertain');
    expect(reconciled['healthy'], isFalse);
  });

  test('non-pepper detail result is never overridden', () {
    final reconciled = AiPestService.applyKnownPest(
      _analysisJson(isPepperPlant: false),
      'Pterolopha annulata',
    );

    expect(reconciled['pest_type'], 'Gynaikothrips karny');
    expect(reconciled['is_pepper_plant'], isFalse);
  });

  test('uncertain pest result cannot produce chemical advice', () {
    final uncertain = PestAnalysis.fromJson(
      _analysisJson(pestType: 'Uncertain'),
    );
    final treatment = PestTreatmentEngine.forAnalysis(uncertain, Market.eu);

    expect(treatment.aboveThreshold, isFalse);
    expect(treatment.options.every((option) => !option.isChemical), isTrue);
  });

  testWidgets('uncertain pest uses retake UI instead of treatment UI', (
    tester,
  ) async {
    final uncertain = PestAnalysis.fromJson(
      _analysisJson(pestType: 'Uncertain'),
    );
    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: PestAnalysisScreen(
          imageBytes: base64Decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lE'
            'QVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=',
          ),
          detectedClass: 'Pterolopha annulata',
          prefetch: Future.value(uncertain),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('We could not confirm the pest'), findsOneWidget);
    expect(find.text('Recommended action (IPM)'), findsNothing);
  });
}
