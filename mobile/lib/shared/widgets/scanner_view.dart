import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/services/yolo_detector.dart';
import '../../features/recommendations/ai_detection_service.dart';
import '../../features/recommendations/ai_errors.dart';
import '../../features/recommendations/analysis_ui.dart' show fadeScaleRoute;
import '../../features/recommendations/berry_analysis_screen.dart';
import '../../features/recommendations/leaf_analysis_screen.dart';
import '../../features/recommendations/pest_analysis_screen.dart';
import '../../features/history/history_scope.dart';
import '../../features/history/models/history_record.dart';
import '../../features/history/serialization/history_payload_codec.dart';
import '../../l10n/app_localizations.dart';
import '../models/detection.dart';
import '../models/scanner_model_config.dart';
import 'scan_result_view.dart';

/// Camera screen for one model: frame the plant, tap the shutter, see what the
/// model found.
///
/// The flow is deliberately one-shot rather than a live stream. A still capture
/// is higher resolution than a preview frame, the user controls exactly what
/// gets analysed, and inference runs once instead of continuously — which
/// matters because it occupies the UI isolate (see [YoloDetector]).
class ScannerView extends StatefulWidget {
  final ScannerModelConfig modelConfig;
  final List<ScannerModelConfig> additionalFallbackConfigs;
  final String title;

  const ScannerView({
    super.key,
    required this.modelConfig,
    this.additionalFallbackConfigs = const [],
    required this.title,
  });

  @override
  State<ScannerView> createState() => _ScannerViewState();
}

class _ScannerViewState extends State<ScannerView> with WidgetsBindingObserver {
  CameraController? _controller;
  final YoloDetector _detector = YoloDetector(); // kept as offline fallback
  late final List<YoloDetector> _additionalFallbackDetectors;
  final AiDetectionService _aiDetector = AiDetectionService();
  bool _disposed = false;

  /// Shown once on entry so the "how to scan" sheet doesn't pop up repeatedly.
  bool _instructionsShown = false;

  /// True from shutter press until the result is ready.
  bool _analyzing = false;

  /// Rotating status line shown over the analysing overlay so a long cloud call
  /// never reads as frozen. Cycled by [_statusTimer] while [_analyzing].
  String _status = '';
  Timer? _statusTimer;

  static List<String> _statusMessages(AppLocalizations t) => [
    t.statusThinking,
    t.statusValidating,
    t.statusInspecting,
    t.statusMatching,
    t.statusCloserLook,
    t.statusAlmostThere,
  ];

  /// Localized display label for this scanner (used in the hint + result badge).
  String _localizedLabel(AppLocalizations t) {
    switch (widget.modelConfig.id) {
      case 'berry':
        return t.berryLabel;
      case 'pest':
        return t.pestLabel;
      case 'plant':
        return t.plantLabel;
      default:
        return t.leafLabel;
    }
  }

  /// Set once a photo has been captured and analysed.
  Uint8List? _photo;
  DetectionResult? _result;
  String? _historyRecordKey;

  String? _modelError;
  String? _cameraError;

  /// Orientations to restore on the way out. The scanner locks to portrait
  /// because the preview cover-fit assumes it, but the lock is process-wide —
  /// leaving it set would pin the rest of the app (notably the grading flow)
  /// to portrait for the remainder of the session.
  static const _defaultOrientations = <DeviceOrientation>[
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
    DeviceOrientation.landscapeLeft,
    DeviceOrientation.landscapeRight,
  ];

  @override
  void initState() {
    super.initState();
    _additionalFallbackDetectors = List.generate(
      widget.additionalFallbackConfigs.length,
      (_) => YoloDetector(),
    );
    WidgetsBinding.instance.addObserver(this);
    SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
    _bootstrap();
    // Show the localized "how to scan" guide before the user starts. The camera
    // keeps initialising behind the sheet, so it's ready when they tap start.
    WidgetsBinding.instance.addPostFrameCallback((_) => _showInstructions());
  }

  void _showInstructions({bool force = false}) {
    if (_disposed || !mounted) return;
    if (_instructionsShown && !force) return;
    _instructionsShown = true;
    final t = AppLocalizations.of(context);
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (ctx) => _InstructionsSheet(
        title: t.scanInstructionsTitle,
        steps: [
          t.scanInstructionsStep1(_localizedLabel(t)),
          t.scanInstructionsStep2,
          t.scanInstructionsStep3,
        ],
        startLabel: t.scanInstructionsStart,
        onStart: () => Navigator.of(ctx).pop(),
      ),
    );
  }

  Future<void> _bootstrap() async {
    try {
      final cameras = await availableCameras();
      if (_disposed) return;
      await _initCamera(cameras);
      if (_disposed) return;
      await _detector.load(widget.modelConfig);
      if (_disposed) return;
      for (var i = 0; i < _additionalFallbackDetectors.length; i++) {
        await _additionalFallbackDetectors[i].load(
          widget.additionalFallbackConfigs[i],
        );
        if (_disposed) return;
      }
      AiDetectionService.warmUp(widget.modelConfig.id);
      setState(() {});
    } on CameraException catch (e) {
      if (_disposed) return;
      setState(() => _cameraError = e.description ?? e.code);
    } catch (e) {
      if (_disposed) return;
      setState(() => _modelError = e.toString());
    }
  }

  Future<void> _initCamera(List<CameraDescription> cameras) async {
    if (cameras.isEmpty) {
      throw CameraException('no_camera', 'No camera found on this device.');
    }
    final back = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.back,
      orElse: () => cameras.first,
    );
    // Stills can afford more pixels than a 30fps preview could. The detector
    // letterboxes to 640 anyway, so going beyond ~720p costs decode time
    // without improving detections.
    final controller = CameraController(
      back,
      ResolutionPreset.high,
      enableAudio: false,
    );
    await controller.initialize();
    if (_disposed) return;
    setState(() => _controller = controller);
  }

  Future<void> _capture() async {
    final controller = _controller;
    if (controller == null || _analyzing || !_detector.isReady) return;
    setState(() => _analyzing = true);
    _startStatusCycle();
    try {
      final shot = await controller.takePicture();
      _historyRecordKey = newHistoryRecordKey();
      await _analyzeBytes(await shot.readAsBytes());
    } catch (e, st) {
      _onAnalyzeError(e, st);
    }
  }

  /// Picks an existing photo from the gallery and analyses it with the same
  /// pipeline as a live capture.
  Future<void> _pickFromGallery() async {
    if (_analyzing || !_detector.isReady) return;
    setState(() => _analyzing = true);
    _startStatusCycle();
    try {
      final picked = await ImagePicker().pickImage(
        source: ImageSource.gallery,
        maxWidth: 2000,
      );
      if (picked == null) {
        _stopStatusCycle();
        if (!_disposed) setState(() => _analyzing = false);
        return;
      }
      _historyRecordKey = newHistoryRecordKey();
      await _analyzeBytes(await picked.readAsBytes());
    } catch (e, st) {
      _onAnalyzeError(e, st);
    }
  }

  /// Shared detection path for both camera capture and gallery pick.
  Future<void> _analyzeBytes(Uint8List bytes) async {
    // All configured local detectors and Gemini run concurrently. Most
    // scanners have one local model; the combined plant scanner adds the
    // original pest model beside the original leaf model. The merged future is
    // shared with Claude's priors and the cloud-failure fallback, so no model is
    // run twice.
    final localDetectors = [_detector, ..._additionalFallbackDetectors];
    final Future<DetectionResult?> yoloFuture =
        Future.wait(
          localDetectors.map(
            (detector) => detector.isReady
                ? detector
                      .detectJpeg(bytes, 0)
                      .then<DetectionResult?>((result) => result)
                      .catchError((_) => null)
                : Future<DetectionResult?>.value(null),
          ),
        ).then((results) {
          final available = results.whereType<DetectionResult>().toList();
          return available.isEmpty ? null : mergeDetectionResults(available);
        });

    // Primary path: AI detection (multi-object, higher accuracy), informed by
    // the trained model's priors. Falls back to the YOLO result on failure.
    DetectionResult result;
    try {
      result = await _aiDetector.detect(
        bytes,
        widget.modelConfig,
        yolo: yoloFuture,
      );
    } catch (e, st) {
      // Surface why the AI path failed — otherwise a Gemini error silently
      // falls back to YOLO and looks like a slow success.
      logAiError('scanner-ai-${widget.modelConfig.id}', e, st);
      final yolo = await yoloFuture ?? await _detector.detectJpeg(bytes, 0);
      if (yolo.frameSize == Size.zero) {
        throw StateError('Could not read that image.');
      }
      result = yolo;
    }
    _stopStatusCycle();
    if (_disposed) return;
    setState(() {
      _photo = bytes;
      _result = result;
      _analyzing = false;
    });
    await _saveDetectionHistory(bytes, result);
  }

  Future<void> _saveDetectionHistory(
    Uint8List bytes,
    DetectionResult result,
  ) async {
    final repository = HistoryScope.maybeOf(context);
    if (repository == null) return;
    final key = _historyRecordKey ??= newHistoryRecordKey();
    final primary = _primaryDetection(result);
    try {
      await repository.saveNew(
        recordKey: key,
        feature: _historyFeature(result),
        stage: HistoryAnalysisStage.detection,
        outcomeCode: primary == null
            ? 'no_detection'
            : primary.className.toLowerCase().contains('healthy')
            ? 'healthy'
            : 'detected',
        primaryClassCode: primary?.className,
        imageBytes: bytes,
        resultSchemaVersion: HistoryPayloadCodec.schemaVersion,
        resultJson: HistoryPayloadCodec.detection(result),
        localeCode: Localizations.localeOf(context).languageCode,
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(AppLocalizations.of(context).historySaveFailed)),
      );
    }
  }

  /// Cycles [_status] through [_statusMessages] every couple of seconds so the
  /// analysing overlay stays alive during a long cloud call.
  void _startStatusCycle() {
    final messages = _statusMessages(AppLocalizations.of(context));
    var i = 0;
    setState(() => _status = messages[0]);
    _statusTimer?.cancel();
    _statusTimer = Timer.periodic(const Duration(milliseconds: 2200), (_) {
      i = (i + 1) % messages.length;
      if (!_disposed) setState(() => _status = messages[i]);
    });
  }

  void _stopStatusCycle() {
    _statusTimer?.cancel();
    _statusTimer = null;
  }

  void _onAnalyzeError(Object e, [StackTrace? st]) {
    _stopStatusCycle();
    logAiError('scanner-${widget.modelConfig.id}', e, st);
    if (_disposed) return;
    setState(() => _analyzing = false);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(friendlyAiMessage(e, AppLocalizations.of(context))),
      ),
    );
  }

  void _retake() {
    setState(() {
      _photo = null;
      _result = null;
      _historyRecordKey = null;
    });
    // If the camera was torn down (e.g. the app was backgrounded while the
    // result was showing), bring it back so the preview isn't stuck on a
    // spinner.
    if (_controller == null && !_disposed) _bootstrap();
  }

  /// Opens the AI recommendation screen for the captured [photo], choosing the
  /// flow from the active model — and for the combined 'plant' scanner, from
  /// what was actually detected (pest class → pest flow, else leaf).
  void _showRecommendations(Uint8List photo) {
    // The recommendation is a separate API call made when this screen opens
    // (on the button tap), not prefetched during the scan.
    final top = _topDetection();
    final detectedLeaf =
        top != null &&
            !top.className.toLowerCase().contains('healthy') &&
            !AiDetectionService.isPestClass(top.className)
        ? top.className
        : null;
    // Mirror the leaf handoff for pests: a normal-confidence scanner label is
    // carried into the detail analysis so the second AI request measures
    // count/severity without silently changing the pest species. Relaxed local
    // matches remain unanchored and must be independently verified.
    final detectedPest = detectedPestForRecommendations(
      top,
      lowConfidence: _result?.lowConfidence ?? false,
    );

    final Widget page;
    switch (widget.modelConfig.id) {
      case 'berry':
        page = BerryAnalysisScreen(
          imageBytes: photo,
          historyRecordKey: _historyRecordKey,
        );
      case 'pest':
        page = PestAnalysisScreen(
          imageBytes: photo,
          detectedClass: detectedPest,
          historyRecordKey: _historyRecordKey,
        );
      case 'plant':
        page = top != null && AiDetectionService.isPestClass(top.className)
            ? PestAnalysisScreen(
                imageBytes: photo,
                detectedClass: detectedPest,
                historyRecordKey: _historyRecordKey,
              )
            : LeafAnalysisScreen(
                imageBytes: photo,
                detectedClass: detectedLeaf,
                historyRecordKey: _historyRecordKey,
              );
      default:
        page = LeafAnalysisScreen(
          imageBytes: photo,
          detectedClass: detectedLeaf,
          historyRecordKey: _historyRecordKey,
        );
    }
    Navigator.of(context).push(fadeScaleRoute<void>(page));
  }

  /// For the combined scanner: route by the most-confident non-healthy
  /// detection — a pest class sends the user to the pest flow, otherwise leaf.
  Detection? _topDetection() {
    final dets = _result?.detections ?? const [];
    final problems =
        dets
            .where((d) => !d.className.toLowerCase().contains('healthy'))
            .toList()
          ..sort((a, b) => b.score.compareTo(a.score));
    return problems.isNotEmpty
        ? problems.first
        : (dets.isNotEmpty ? dets.first : null);
  }

  Detection? _primaryDetection(DetectionResult result) {
    if (result.detections.isEmpty) return null;
    final sorted = [...result.detections]
      ..sort((a, b) => b.score.compareTo(a.score));
    return sorted.first;
  }

  HistoryFeature _historyFeature(DetectionResult result) {
    switch (widget.modelConfig.id) {
      case 'berry':
        return HistoryFeature.berryDisease;
      case 'pest':
        return HistoryFeature.pestDetection;
      case 'leaf':
        return HistoryFeature.leafDisease;
      default:
        final problems =
            result.detections
                .where(
                  (detection) =>
                      !detection.className.toLowerCase().contains('healthy'),
                )
                .toList()
              ..sort((a, b) => b.score.compareTo(a.score));
        return problems.isNotEmpty &&
                AiDetectionService.isPestClass(problems.first.className)
            ? HistoryFeature.pestDetection
            : HistoryFeature.leafDisease;
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (_disposed) return;
    if (state == AppLifecycleState.inactive ||
        state == AppLifecycleState.paused) {
      // Backgrounded (e.g. the OS gallery picker opens) → free the camera.
      final controller = _controller;
      if (controller != null && controller.value.isInitialized) {
        controller.dispose();
        if (!_disposed) setState(() => _controller = null);
      }
    } else if (state == AppLifecycleState.resumed) {
      // Re-create the camera we tore down — but only when the preview is what's
      // on screen (not while a captured result is showing, which needs no
      // camera). The old guard returned here when _controller was null, which
      // left the preview permanently dead after returning from the picker.
      if (_controller == null && _photo == null) _bootstrap();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _statusTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    SystemChrome.setPreferredOrientations(_defaultOrientations);
    _controller?.dispose();
    _detector.dispose();
    for (final detector in _additionalFallbackDetectors) {
      detector.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text(widget.title),
        actions: [
          IconButton(
            tooltip: AppLocalizations.of(context).howToScan,
            icon: const Icon(Icons.help_outline),
            onPressed: () => _showInstructions(force: true),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    final t = AppLocalizations.of(context);
    if (_cameraError != null) {
      return _message(
        icon: Icons.no_photography_outlined,
        title: t.cameraUnavailable,
        detail: t.errGeneric,
      );
    }

    if (_modelError != null) {
      return _message(
        icon: Icons.download_for_offline_outlined,
        title: t.modelLoadFailed(_localizedLabel(t)),
        detail: t.otherScanTypesUnaffected,
      );
    }

    final photo = _photo;
    final result = _result;
    if (photo != null && result != null) {
      return ScanResultView(
        photo: photo,
        result: result,
        modelLabel: _localizedLabel(t),
        onRetake: _retake,
        onShowRecommendations: () => _showRecommendations(photo),
      );
    }

    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) {
      return const Center(
        child: CircularProgressIndicator(color: Colors.white),
      );
    }

    return Stack(
      fit: StackFit.expand,
      children: [
        _CoveredPreview(controller: controller),
        if (_analyzing)
          Container(
            color: Colors.black54,
            alignment: Alignment.center,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const CircularProgressIndicator(color: Colors.white),
                const SizedBox(height: 16),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  child: Text(
                    _status,
                    key: ValueKey(_status),
                    style: const TextStyle(color: Colors.white, fontSize: 16),
                  ),
                ),
              ],
            ),
          ),
        _buildShutterBar(),
      ],
    );
  }

  Widget _buildShutterBar() {
    final t = AppLocalizations.of(context);
    final ready = _detector.isReady && !_analyzing;
    return SafeArea(
      child: Align(
        alignment: Alignment.bottomCenter,
        child: Padding(
          padding: const EdgeInsets.only(bottom: 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  ready ? t.scanHint(_localizedLabel(t)) : t.preparing,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _CircleAction(
                    icon: Icons.photo_library_outlined,
                    onPressed: ready ? _pickFromGallery : null,
                  ),
                  const SizedBox(width: 32),
                  _ShutterButton(
                    semanticLabel: t.captureAndScan,
                    onPressed: ready ? _capture : null,
                  ),
                  const SizedBox(width: 32),
                  // Invisible twin keeps the shutter optically centered.
                  const Opacity(
                    opacity: 0,
                    child: IgnorePointer(
                      child: _CircleAction(icon: Icons.photo_library_outlined),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _message({
    required IconData icon,
    required String title,
    required String detail,
  }) {
    return Container(
      color: Colors.black87,
      alignment: Alignment.center,
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: Colors.white70, size: 56),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          Text(
            detail,
            style: const TextStyle(
              color: Colors.white54,
              height: 1.4,
              fontSize: 13,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

/// Combines independent local-model outputs for a shared scanner.
///
/// Each detection keeps the class name, score, box, and color produced by its
/// source model. The models run in parallel, so the combined duration is the
/// longest individual duration rather than their sum. A relaxed match from
/// either model keeps the combined result marked low-confidence.
@visibleForTesting
DetectionResult mergeDetectionResults(List<DetectionResult> results) {
  if (results.isEmpty) {
    return const DetectionResult([], Size.zero, 0);
  }

  var frameSize = Size.zero;
  var inferenceMs = 0;
  var thresholdUsed = double.infinity;
  var lowConfidence = false;
  final detections = <Detection>[];

  for (final result in results) {
    detections.addAll(result.detections);
    if (frameSize == Size.zero && result.frameSize != Size.zero) {
      frameSize = result.frameSize;
    }
    if (result.inferenceMs > inferenceMs) inferenceMs = result.inferenceMs;
    if (result.thresholdUsed > 0 && result.thresholdUsed < thresholdUsed) {
      thresholdUsed = result.thresholdUsed;
    }
    lowConfidence = lowConfidence || result.lowConfidence;
  }

  return DetectionResult(
    detections,
    frameSize,
    inferenceMs,
    thresholdUsed: thresholdUsed.isFinite ? thresholdUsed : 0,
    lowConfidence: lowConfidence,
  );
}

/// Returns a pest label that is strong enough to anchor detail analysis.
/// Relaxed local matches are intentionally left unanchored so the second-stage
/// analysis can abstain instead of turning a weak guess into treatment advice.
@visibleForTesting
String? detectedPestForRecommendations(
  Detection? detection, {
  required bool lowConfidence,
}) {
  if (detection == null || lowConfidence) return null;
  return AiDetectionService.isPestClass(detection.className)
      ? detection.className
      : null;
}

/// Localized "how to scan" guide shown in a bottom sheet before the user starts.
class _InstructionsSheet extends StatelessWidget {
  final String title;
  final List<String> steps;
  final String startLabel;
  final VoidCallback onStart;

  const _InstructionsSheet({
    required this.title,
    required this.steps,
    required this.startLabel,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(
          20,
          4,
          20,
          20 + MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(Icons.center_focus_strong, color: cs.primary),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            for (int i = 0; i < steps.length; i++)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 26,
                      height: 26,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: cs.primary.withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                      ),
                      child: Text(
                        '${i + 1}',
                        style: TextStyle(
                          color: cs.primary,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Text(
                        steps[i],
                        style: TextStyle(
                          color: cs.onSurface,
                          height: 1.4,
                          fontSize: 15,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 4),
            FilledButton(
              onPressed: onStart,
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              child: Text(startLabel),
            ),
          ],
        ),
      ),
    );
  }
}

/// A circular translucent action button (used for the gallery picker).
class _CircleAction extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;

  const _CircleAction({required this.icon, this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.black45,
      shape: const CircleBorder(),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onPressed,
        child: SizedBox(
          width: 52,
          height: 52,
          child: Icon(
            icon,
            color: onPressed == null ? Colors.white54 : Colors.white,
          ),
        ),
      ),
    );
  }
}

class _ShutterButton extends StatelessWidget {
  final String semanticLabel;
  final VoidCallback? onPressed;

  const _ShutterButton({required this.semanticLabel, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null;
    return Semantics(
      button: true,
      label: semanticLabel,
      child: GestureDetector(
        onTap: onPressed,
        child: AnimatedOpacity(
          duration: const Duration(milliseconds: 150),
          opacity: enabled ? 1.0 : 0.4,
          child: Container(
            width: 76,
            height: 76,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 4),
            ),
            child: Container(
              margin: const EdgeInsets.all(6),
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Fills the screen with the preview using [BoxFit.cover].
class _CoveredPreview extends StatelessWidget {
  final CameraController controller;
  const _CoveredPreview({required this.controller});

  @override
  Widget build(BuildContext context) {
    final preview = controller.value.previewSize!;
    // previewSize is in sensor (landscape) orientation; swap for portrait.
    return ClipRect(
      child: SizedBox.expand(
        child: FittedBox(
          fit: BoxFit.cover,
          child: SizedBox(
            width: preview.height,
            height: preview.width,
            child: CameraPreview(controller),
          ),
        ),
      ),
    );
  }
}
