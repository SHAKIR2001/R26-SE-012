import 'dart:isolate';
import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui';

import 'package:flutter/foundation.dart' show kIsWeb, visibleForTesting;
import 'package:flutter/services.dart' show rootBundle;
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

import '../../shared/models/detection.dart';
import '../../shared/models/scanner_model_config.dart';

/// Letterbox geometry for fitting a `uw x uh` frame into a square
/// `inputSize x inputSize` tensor without distorting the aspect ratio.
///
/// The frame is scaled down until its longest side fits, then centered, with
/// the leftover margin padded. [decode] uses the same numbers in reverse to map
/// model-space boxes back onto the original frame, so the two must stay in
/// sync.
class LetterboxGeometry {
  /// Ratio applied to the source frame. Always <= 1 for frames larger than the
  /// input.
  final double scale;

  /// Size of the scaled frame, before padding.
  final int scaledWidth;
  final int scaledHeight;

  /// Padding on the left and top edges. The right/bottom edges absorb any odd
  /// leftover pixel, which is why these use truncating division.
  final int padX;
  final int padY;

  const LetterboxGeometry({
    required this.scale,
    required this.scaledWidth,
    required this.scaledHeight,
    required this.padX,
    required this.padY,
  });

  factory LetterboxGeometry.forFrame({
    required int frameWidth,
    required int frameHeight,
    required int inputSize,
  }) {
    final scale = inputSize / math.max(frameWidth, frameHeight);
    final scaledWidth = (frameWidth * scale).round();
    final scaledHeight = (frameHeight * scale).round();
    return LetterboxGeometry(
      scale: scale,
      scaledWidth: scaledWidth,
      scaledHeight: scaledHeight,
      padX: (inputSize - scaledWidth) ~/ 2,
      padY: (inputSize - scaledHeight) ~/ 2,
    );
  }
}

/// Loads one YOLOv8 TFLite model and runs detection on camera frames.
///
/// All three shipped models share the same I/O contract:
///   input  : float32 [1, 3, 640, 640]  (NCHW, RGB, /255, letterboxed)
///   output : float32 [1, 4 + numClasses, 8400]  (rows: cx,cy,w,h, then scores)
///
/// ## Runtime constraints — do not "clean these up"
///
/// Three workarounds below are load-bearing. Each was found the hard way, and
/// each fails as an opaque native error with no useful Dart stack trace:
///
///  1. Inference runs on the **calling isolate**, not an [IsolateInterpreter].
///     tflite_flutter 0.12.1's IsolateInterpreter rebuilds the interpreter from
///     its native address on every run, so invoke() fails. This is tolerable
///     because the camera preview is a native SurfaceView: live video keeps
///     rendering even while a frame occupies the UI isolate, and only the box
///     overlay updates in bursts.
///
///  2. Tensors are driven **directly** (setTo/invoke/getOutputTensor), never
///     via [Interpreter.run]. run() infers the input shape from a nested list
///     and mis-detects our NCHW Float32List, firing a spurious
///     resizeInputTensor that corrupts the graph. It surfaces later as
///     "Input tensor lacks data" at invoke.
///
///  3. The bundled .tflite assets must be **repacked** before shipping. The
///     LiteRT exporter stores large weight buffers by offset outside the
///     flatbuffer, which this runtime cannot read ("Bad state: failed
///     precondition"). The assets in this repo are already repacked; re-run
///     `pepper_care_app/tools/repack_tflite.py` only if the models are
///     re-exported from Ultralytics.
class YoloDetector {
  static const int inputSize = 640;
  static const int numAnchors = 8400;

  Interpreter? _interpreter;
  ScannerModelConfig? _config;

  /// Raw model bytes, cached so [detectJpeg] can rebuild an interpreter inside a
  /// background isolate (a native [Interpreter] handle can't be sent across
  /// isolates, but the bytes can).
  Uint8List? _modelBytes;

  /// Score a class must beat for a detection to be reported normally.
  double confThreshold;

  /// Overlap above which NMS suppresses the lower-scoring of two boxes.
  double iouThreshold;

  /// Relaxed threshold used for a second pass when [confThreshold] yields
  /// nothing at all.
  ///
  /// A single deliberate photo has no next frame to redeem a near miss: if the
  /// best score was 0.48 the user would just see "Nothing detected" and have no
  /// idea the model nearly fired. Rather than lower the bar for every scan, the
  /// bar drops only when the strict pass comes back empty, and the result is
  /// flagged so the UI can present it as tentative.
  ///
  /// Set to a value >= [confThreshold] to disable the second pass.
  double fallbackConfThreshold;

  YoloDetector({
    this.confThreshold = 0.5,
    this.iouThreshold = 0.45,
    this.fallbackConfThreshold = 0.2,
  });

  ScannerModelConfig? get config => _config;
  bool get isReady => _interpreter != null;

  /// Loads [config]. Throws [StateError] if the tensor shapes don't match the
  /// contract above.
  ///
  /// This validation deliberately throws rather than asserting: asserts are
  /// stripped in release builds, and a mismatched model would then silently
  /// produce garbage detections in production instead of failing loudly.
  Future<void> load(ScannerModelConfig config) async {
    await dispose();

    // Load the bytes once: used to validate on the main isolate here, and cached
    // so each scan can spin up a short-lived interpreter in a background isolate.
    final bytes = (await rootBundle.load(
      config.assetPath,
    )).buffer.asUint8List();
    final interpreter = Interpreter.fromBuffer(
      bytes,
      options: InterpreterOptions()..threads = 4,
    );

    final inShape = interpreter.getInputTensor(0).shape;
    final outShape = interpreter.getOutputTensor(0).shape;
    if (inShape.length != 4 ||
        inShape[1] != 3 ||
        inShape[2] != inputSize ||
        inShape[3] != inputSize) {
      throw StateError(
        'Unexpected input shape $inShape '
        '(expected [1, 3, $inputSize, $inputSize])',
      );
    }
    if (outShape.length != 3 ||
        outShape[1] != config.outputChannels ||
        outShape[2] != numAnchors) {
      throw StateError(
        'Unexpected output shape $outShape '
        '(expected [1, ${config.outputChannels}, $numAnchors])',
      );
    }

    // Pin the input shape and (re)allocate so the input buffer is guaranteed to
    // exist before the first setTo()/invoke().
    interpreter.resizeInputTensor(0, [1, 3, inputSize, inputSize]);
    interpreter.allocateTensors();

    _interpreter = interpreter;
    _modelBytes = bytes;
    _config = config;
  }

  Future<void> dispose() async {
    _interpreter?.close();
    _interpreter = null;
    _modelBytes = null;
    _config = null;
  }

  /// Decodes [jpegBytes] and runs the full detection pipeline **in a background
  /// isolate**, so the heavy pixel loop and native invoke() never block the UI
  /// thread (a one-shot scan would otherwise freeze the app for a second or more).
  ///
  /// Spins up a short-lived interpreter from the cached model bytes for each
  /// scan. That's a few ms of load cost, traded for a responsive UI.
  // ponytail: fresh interpreter per scan; use a persistent worker isolate if
  // scan throughput ever matters.
  Future<DetectionResult> detectJpeg(
    Uint8List jpegBytes,
    int sensorOrientation,
  ) {
    final cfg = _config;
    final bytes = _modelBytes;
    if (cfg == null || bytes == null) {
      return Future.value(const DetectionResult([], Size.zero, 0));
    }
    // Copy into locals so the isolate closure captures only sendable data, never
    // `this` (which holds a non-sendable native interpreter handle).
    final args = _DetectArgs(
      modelBytes: bytes,
      config: cfg,
      jpegBytes: jpegBytes,
      sensorOrientation: sensorOrientation,
      conf: confThreshold,
      iou: iouThreshold,
      fallback: fallbackConfThreshold,
    );
    // Flutter web does not provide worker-isolate semantics compatible with
    // this native interpreter path. Keep the same inference implementation but
    // execute it directly so the existing browser grading flow still builds.
    return kIsWeb
        ? _detectInIsolate(args)
        : Isolate.run(() => _detectInIsolate(args));
  }

  /// Runs detection on one already-decoded RGB frame.
  ///
  /// [sensorOrientation] rotates the sensor frame upright (degrees, clockwise).
  /// Returns boxes normalized 0..1 in the upright frame, plus that frame's
  /// [Size] so the overlay can cover-fit them onto the preview.
  ///
  /// The reported duration covers the **whole** pipeline, not just invoke():
  /// rotation and YUV conversion typically dominate, so timing invoke() alone
  /// would badly understate real per-frame cost.
  Future<DetectionResult> detect(img.Image frame, int sensorOrientation) async {
    final cfg = _config;
    final interpreter = _interpreter;
    if (cfg == null || interpreter == null) {
      return const DetectionResult([], Size.zero, 0);
    }

    final sw = Stopwatch()..start();

    // 1. Rotate the sensor frame upright to match the portrait preview.
    final upright = sensorOrientation == 0
        ? frame
        : img.copyRotate(frame, angle: sensorOrientation);
    final uw = upright.width;
    final uh = upright.height;

    // 2. Letterbox to 640x640 (keep aspect ratio, pad gray 114).
    final box = LetterboxGeometry.forFrame(
      frameWidth: uw,
      frameHeight: uh,
      inputSize: inputSize,
    );
    final resized = img.copyResize(
      upright,
      width: box.scaledWidth,
      height: box.scaledHeight,
    );

    final canvas = img.Image(width: inputSize, height: inputSize);
    img.fill(canvas, color: img.ColorRgb8(114, 114, 114));
    img.compositeImage(canvas, resized, dstX: box.padX, dstY: box.padY);

    // 3. Build the NCHW float32 tensor (all R, then all G, then all B).
    final tensor = Float32List(3 * inputSize * inputSize);
    const plane = inputSize * inputSize;
    int i = 0;
    for (int y = 0; y < inputSize; y++) {
      for (int x = 0; x < inputSize; x++) {
        final px = canvas.getPixel(x, y);
        tensor[i] = px.r / 255.0;
        tensor[plane + i] = px.g / 255.0;
        tensor[2 * plane + i] = px.b / 255.0;
        i++;
      }
    }

    // 4. Inference. See constraint 2 in the class doc: drive the tensors
    // directly, never Interpreter.run().
    interpreter.getInputTensor(0).setTo(tensor);
    interpreter.invoke();
    final outBytes = interpreter.getOutputTensor(0).data;
    final output = outBytes.buffer.asFloat32List(
      outBytes.offsetInBytes,
      cfg.outputChannels * numAnchors,
    );

    // 5. Decode -> normalize -> NMS, with a relaxed retry if nothing hits.
    final outcome = decodeWithFallback(output, cfg, uw, uh, box);
    sw.stop();

    return DetectionResult(
      outcome.detections,
      Size(uw.toDouble(), uh.toDouble()),
      sw.elapsedMilliseconds,
      thresholdUsed: outcome.threshold,
      lowConfidence: outcome.usedFallback,
    );
  }

  /// Decodes at [confThreshold]; if that finds nothing, decodes the same buffer
  /// again at [fallbackConfThreshold].
  ///
  /// The retry is cheap — it re-reads an output tensor that is already in
  /// memory, costing one more pass over 8400 anchors rather than another
  /// inference. It only runs when the strict pass is empty, so a normal scan
  /// pays nothing.
  ///
  /// `usedFallback` is true only when the relaxed pass actually produced
  /// detections, so an empty result is never mislabelled as low-confidence.
  @visibleForTesting
  DecodeOutcome decodeWithFallback(
    Float32List out,
    ScannerModelConfig cfg,
    int uw,
    int uh,
    LetterboxGeometry box,
  ) {
    final strict = decode(out, cfg, uw, uh, box);
    if (strict.isNotEmpty || fallbackConfThreshold >= confThreshold) {
      return (
        detections: strict,
        threshold: confThreshold,
        usedFallback: false,
      );
    }

    final relaxed = decode(
      out,
      cfg,
      uw,
      uh,
      box,
      threshold: fallbackConfThreshold,
    );
    if (relaxed.isEmpty) {
      return (
        detections: relaxed,
        threshold: confThreshold,
        usedFallback: false,
      );
    }
    return (
      detections: relaxed,
      threshold: fallbackConfThreshold,
      usedFallback: true,
    );
  }

  /// Turns a flat model output into normalized, NMS-filtered detections.
  ///
  /// [out] is laid out row-wise: the value for channel `c` at anchor `a` lives
  /// at `out[c * numAnchors + a]`. Rows 0..3 are cx, cy, w, h (normalized to
  /// the letterboxed input); rows 4.. are per-class scores.
  ///
  /// [uw]/[uh] are the upright frame's pixel dimensions, and [box] the geometry
  /// used to letterbox it — both are needed to undo the letterbox.
  ///
  /// [threshold] defaults to [confThreshold]; pass it explicitly to decode the
  /// same buffer at a different bar without mutating the detector.
  @visibleForTesting
  List<Detection> decode(
    Float32List out,
    ScannerModelConfig cfg,
    int uw,
    int uh,
    LetterboxGeometry box, {
    double? threshold,
  }) {
    final minScore = threshold ?? confThreshold;
    final raw = <Detection>[];
    final nc = cfg.numClasses;

    for (int a = 0; a < numAnchors; a++) {
      // argmax over the class rows (4 .. 4+nc-1)
      int bestCls = 0;
      double bestScore = out[4 * numAnchors + a];
      for (int c = 1; c < nc; c++) {
        final s = out[(4 + c) * numAnchors + a];
        if (s > bestScore) {
          bestScore = s;
          bestCls = c;
        }
      }
      if (bestScore < minScore) continue;

      // center-format box, normalized to input -> 640-space -> undo letterbox
      final cx = out[a] * inputSize;
      final cy = out[numAnchors + a] * inputSize;
      final bw = out[2 * numAnchors + a] * inputSize;
      final bh = out[3 * numAnchors + a] * inputSize;

      final x = (cx - bw / 2 - box.padX) / box.scale;
      final y = (cy - bh / 2 - box.padY) / box.scale;
      final w = bw / box.scale;
      final h = bh / box.scale;

      // normalize to 0..1 of the upright frame
      final left = (x / uw).clamp(0.0, 1.0);
      final top = (y / uh).clamp(0.0, 1.0);
      final right = ((x + w) / uw).clamp(0.0, 1.0);
      final bottom = ((y + h) / uh).clamp(0.0, 1.0);

      raw.add(
        Detection(
          classId: bestCls,
          className: cfg.classNames[bestCls],
          score: bestScore,
          rect: Rect.fromLTRB(left, top, right, bottom),
          color: cfg.colorFor(bestCls),
        ),
      );
    }
    return nms(raw, iouThreshold);
  }

  /// Greedy non-maximum suppression. Returns kept boxes, highest score first.
  ///
  /// Copies before sorting so the caller's list is left untouched.
  @visibleForTesting
  List<Detection> nms(List<Detection> dets, double iouThresh) {
    final sorted = List<Detection>.of(dets)
      ..sort((a, b) => b.score.compareTo(a.score));
    final keep = <Detection>[];
    final removed = List<bool>.filled(sorted.length, false);
    for (int i = 0; i < sorted.length; i++) {
      if (removed[i]) continue;
      keep.add(sorted[i]);
      for (int j = i + 1; j < sorted.length; j++) {
        if (!removed[j] && iou(sorted[i].rect, sorted[j].rect) > iouThresh) {
          removed[j] = true;
        }
      }
    }
    return keep;
  }

  /// Intersection over union of two rects. Returns 0 for degenerate input.
  @visibleForTesting
  double iou(Rect a, Rect b) {
    final x1 = math.max(a.left, b.left);
    final y1 = math.max(a.top, b.top);
    final x2 = math.min(a.right, b.right);
    final y2 = math.min(a.bottom, b.bottom);
    final inter = math.max(0.0, x2 - x1) * math.max(0.0, y2 - y1);
    final union = a.width * a.height + b.width * b.height - inter;
    return union <= 0 ? 0 : inter / union;
  }
}

/// Arguments bundled for [_detectInIsolate] — every field is sendable so the
/// whole thing can cross the isolate boundary.
class _DetectArgs {
  final Uint8List modelBytes;
  final ScannerModelConfig config;
  final Uint8List jpegBytes;
  final int sensorOrientation;
  final double conf;
  final double iou;
  final double fallback;
  const _DetectArgs({
    required this.modelBytes,
    required this.config,
    required this.jpegBytes,
    required this.sensorOrientation,
    required this.conf,
    required this.iou,
    required this.fallback,
  });
}

/// Runs the full decode → letterbox → invoke → NMS pipeline on a background
/// isolate, then closes its interpreter. Reuses [YoloDetector.detect] so there's
/// a single source of truth for the detection logic.
Future<DetectionResult> _detectInIsolate(_DetectArgs a) async {
  final decoded = img.decodeImage(a.jpegBytes);
  if (decoded == null) return const DetectionResult([], Size.zero, 0);
  final upright = img.bakeOrientation(decoded);

  final det = YoloDetector(
    confThreshold: a.conf,
    iouThreshold: a.iou,
    fallbackConfThreshold: a.fallback,
  );
  final interpreter = Interpreter.fromBuffer(
    a.modelBytes,
    options: InterpreterOptions()..threads = 4,
  );
  interpreter.resizeInputTensor(0, [
    1,
    3,
    YoloDetector.inputSize,
    YoloDetector.inputSize,
  ]);
  interpreter.allocateTensors();
  det._interpreter = interpreter;
  det._config = a.config;
  try {
    return await det.detect(upright, a.sensorOrientation);
  } finally {
    interpreter.close();
  }
}

/// What one decode pass produced, and at what bar.
typedef DecodeOutcome = ({
  List<Detection> detections,
  double threshold,
  bool usedFallback,
});

/// Result of one detection pass.
class DetectionResult {
  final List<Detection> detections;

  /// Upright frame size in pixels; the overlay fits boxes onto this.
  final Size frameSize;

  /// Wall time for the full pipeline (rotate + letterbox + invoke + decode).
  final int inferenceMs;

  /// Confidence bar these detections actually cleared.
  final double thresholdUsed;

  /// True when nothing met the normal threshold and these came from the
  /// relaxed second pass. The UI must say so — a 25% match presented like a
  /// 90% one would mislead.
  final bool lowConfidence;

  const DetectionResult(
    this.detections,
    this.frameSize,
    this.inferenceMs, {
    this.thresholdUsed = 0,
    this.lowConfidence = false,
  });
}
