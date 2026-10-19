import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/core/services/yolo_detector.dart';
import 'package:pepper_care/shared/models/detection.dart';
import 'package:pepper_care/shared/widgets/scanner_view.dart';

void main() {
  test('combined fallback preserves detections from leaf and pest models', () {
    const leaf = Detection(
      classId: 1,
      className: 'Leaf Blight',
      score: 0.82,
      rect: Rect.fromLTWH(0.1, 0.1, 0.3, 0.3),
      color: Color(0xFFE74C3C),
    );
    const pest = Detection(
      classId: 0,
      className: 'Diconocoris distanti',
      score: 0.91,
      rect: Rect.fromLTWH(0.5, 0.2, 0.2, 0.2),
      color: Color(0xFFE74C3C),
    );

    final merged = mergeDetectionResults(const [
      DetectionResult([leaf], Size(1200, 900), 80, thresholdUsed: 0.5),
      DetectionResult([pest], Size(1200, 900), 110, thresholdUsed: 0.5),
    ]);

    expect(merged.detections, containsAll([leaf, pest]));
    expect(merged.frameSize, const Size(1200, 900));
    expect(merged.inferenceMs, 110);
    expect(merged.thresholdUsed, 0.5);
    expect(merged.lowConfidence, isFalse);
  });

  test('combined fallback conservatively retains low-confidence state', () {
    final merged = mergeDetectionResults(const [
      DetectionResult([], Size(640, 640), 30, thresholdUsed: 0.5),
      DetectionResult(
        [],
        Size(640, 640),
        45,
        thresholdUsed: 0.2,
        lowConfidence: true,
      ),
    ]);

    expect(merged.lowConfidence, isTrue);
    expect(merged.thresholdUsed, 0.2);
  });
}
