import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:pepper_care/core/services/yolo_detector.dart';
import 'package:pepper_care/l10n/app_localizations.dart';
import 'package:pepper_care/shared/models/detection.dart';
import 'package:pepper_care/shared/widgets/scan_result_view.dart';

/// A real 8x8 PNG, so Image.memory has something valid to decode.
Uint8List tinyPng() =>
    Uint8List.fromList(img.encodePng(img.Image(width: 8, height: 8)));

Detection det(String name, double score) => Detection(
  classId: 0,
  className: name,
  score: score,
  rect: const Rect.fromLTRB(0.1, 0.1, 0.5, 0.5),
  color: const Color(0xFF2ECC71),
);

Widget wrap(Widget child) => MaterialApp(
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  home: Scaffold(body: child),
);

void main() {
  group('ScanResultView', () {
    testWidgets('lists every detection with its confidence', (tester) async {
      await tester.pumpWidget(
        wrap(
          ScanResultView(
            photo: tinyPng(),
            result: DetectionResult(
              [det('lace_bug_damage', 0.91), det('healthy_berry', 0.62)],
              const Size(640, 480),
              42,
            ),
            modelLabel: 'Berry',
            onRetake: () {},
          ),
        ),
      );

      expect(find.text('2 findings'), findsOneWidget);
      expect(find.text('Lace bug damage'), findsOneWidget);
      expect(find.text('91%'), findsOneWidget);
      expect(find.text('Healthy berry'), findsOneWidget);
      expect(find.text('62%'), findsOneWidget);
      expect(find.textContaining('42ms'), findsNothing);
    });

    testWidgets('uses the singular for a single finding', (tester) async {
      await tester.pumpWidget(
        wrap(
          ScanResultView(
            photo: tinyPng(),
            result: DetectionResult(
              [det('healthy_berry', 0.8)],
              const Size(640, 480),
              10,
            ),
            modelLabel: 'Berry',
            onRetake: () {},
          ),
        ),
      );

      expect(find.text('1 finding'), findsOneWidget);
    });

    testWidgets('explains what to try when nothing is detected', (
      tester,
    ) async {
      await tester.pumpWidget(
        wrap(
          ScanResultView(
            photo: tinyPng(),
            result: const DetectionResult([], Size(640, 480), 12),
            modelLabel: 'Leaf',
            onRetake: () {},
          ),
        ),
      );

      expect(find.text('Nothing detected'), findsOneWidget);
      expect(find.textContaining('Try moving closer'), findsOneWidget);
    });

    testWidgets('warns when results came from the relaxed pass', (
      tester,
    ) async {
      await tester.pumpWidget(
        wrap(
          ScanResultView(
            photo: tinyPng(),
            result: DetectionResult(
              [det('Quick Wilt', 0.28)],
              const Size(640, 480),
              33,
              thresholdUsed: 0.2,
              lowConfidence: true,
            ),
            modelLabel: 'Leaf',
            onRetake: () {},
          ),
        ),
      );

      expect(find.textContaining('Low confidence'), findsOneWidget);
      expect(find.text('Quick Wilt'), findsOneWidget);
      expect(find.text('28%'), findsOneWidget);
    });

    testWidgets('stays quiet for a normal-confidence result', (tester) async {
      await tester.pumpWidget(
        wrap(
          ScanResultView(
            photo: tinyPng(),
            result: DetectionResult(
              [det('healthy_berry', 0.88)],
              const Size(640, 480),
              33,
              thresholdUsed: 0.5,
            ),
            modelLabel: 'Berry',
            onRetake: () {},
          ),
        ),
      );

      expect(find.textContaining('Low confidence'), findsNothing);
    });

    testWidgets('retake button fires its callback', (tester) async {
      var retaken = false;
      await tester.pumpWidget(
        wrap(
          ScanResultView(
            photo: tinyPng(),
            result: const DetectionResult([], Size(640, 480), 5),
            modelLabel: 'Pest',
            onRetake: () => retaken = true,
          ),
        ),
      );

      await tester.tap(find.text('Take another photo'));
      await tester.pump();

      expect(retaken, isTrue);
    });
  });
}
