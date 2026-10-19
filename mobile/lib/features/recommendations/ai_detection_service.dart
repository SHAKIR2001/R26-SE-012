import 'dart:convert';
import 'dart:isolate';
import 'dart:async';

import 'package:flutter/foundation.dart'
    show debugPrint, kIsWeb, visibleForTesting;
import 'package:flutter/services.dart';
import 'package:google_generative_ai/google_generative_ai.dart' show Schema;
import 'package:http/http.dart' as http;
import 'package:image/image.dart' as img;

import '../../core/services/yolo_detector.dart' show DetectionResult;
import '../../shared/models/detection.dart';
import '../../shared/models/scanner_model_config.dart';
import 'ai_config.dart';
import 'ai_leaf_service.dart' show LeafAnalysisException;
import 'claude_classifier_service.dart';

Future<T> _runOffThread<T>(FutureOr<T> Function() work) =>
    kIsWeb ? Future<T>.sync(work) : Isolate.run(work);

/// Runs multi-object detection with the AI: given a captured photo it finds
/// every object (e.g. each leaf), draws a box, and classifies it — returning a
/// [DetectionResult] that drops straight into the existing overlay/result view.
///
/// Per-class reference images from assets/data are sent as labeled exemplars so
/// the classification is grounded in real examples of each class.
class AiDetectionService {
  // domain id -> ordered [className, reference folder]. Class names match the
  // ScannerModelConfig class lists so labels/colors line up.
  static const Map<String, List<List<String>>> _refs = {
    'leaf': [
      // NOTE: the on-disk folders are mislabeled — blight/ actually holds Quick
      // Wilt photos (tip/margin dieback) and quick/ holds Leaf Blight photos
      // (discrete spots). We map each LABEL to the folder that truly contains it.
      ['Leaf Blight', 'assets/data/leaf/quick/'],
      ['Quick Wilt', 'assets/data/leaf/blight/'],
      ['Little Leaf', 'assets/data/leaf/little/'],
      ['Healthy leaves', 'assets/data/leaf/healthy/'],
    ],
    'berry': [
      ['lace_bug_damage', 'assets/data/berry/lace/'],
      ['healthy_berry', 'assets/data/berry/healthy/'],
    ],
    'pest': [
      ['Diconocoris distanti', 'assets/data/phest/diconocoris/'],
      ['Gynaikothrips karny', 'assets/data/phest/gynaikothrips/'],
      ['Pterolopha annulata', 'assets/data/phest/pterolopha/'],
      ['healthy', 'assets/data/phest/healthy/'],
    ],
    // Combined leaf + pest domain: the AI decides leaf-vs-pest, then the class.
    'plant': [
      // Same folder-label swap as the 'leaf' domain above (blight/ ↔ quick/).
      ['Leaf Blight', 'assets/data/leaf/quick/'],
      ['Quick Wilt', 'assets/data/leaf/blight/'],
      ['Little Leaf', 'assets/data/leaf/little/'],
      ['Healthy leaves', 'assets/data/leaf/healthy/'],
      ['Diconocoris distanti', 'assets/data/phest/diconocoris/'],
      ['Gynaikothrips karny', 'assets/data/phest/gynaikothrips/'],
      ['Pterolopha annulata', 'assets/data/phest/pterolopha/'],
      ['healthy', 'assets/data/phest/healthy/'],
    ],
  };

  // Combined-domain class sets + colors (used when config.id == 'plant').
  static const List<String> leafClasses = [
    'Healthy leaves',
    'Leaf Blight',
    'Little Leaf',
    'Quick Wilt',
  ];
  static const List<String> pestClasses = [
    'Diconocoris distanti',
    'Gynaikothrips karny',
    'Pterolopha annulata',
    'healthy',
  ];
  static const Map<String, Color> _plantColors = {
    'Healthy leaves': Color(0xFF2ECC71),
    'Leaf Blight': Color(0xFFE74C3C),
    'Little Leaf': Color(0xFFE67E22),
    'Quick Wilt': Color(0xFF9B59B6),
    'Diconocoris distanti': Color(0xFFE74C3C),
    'Gynaikothrips karny': Color(0xFFE67E22),
    'Pterolopha annulata': Color(0xFF9B59B6),
    'healthy': Color(0xFF2ECC71),
  };

  /// True if [className] is one of the pest classes (vs a leaf-disease class).
  static bool isPestClass(String className) => pestClasses.contains(className);

  @visibleForTesting
  static String? referenceFolderForTesting(String domainId, String className) {
    for (final entry in _refs[domainId] ?? const <List<String>>[]) {
      if (entry[0] == className) return entry[1];
    }
    return null;
  }

  @visibleForTesting
  static int exemplarLimitForTesting(String domainId) =>
      _exemplarLimit(domainId);

  // Cache of resized reference exemplars per domain, loaded once.
  static final Map<String, List<_Exemplar>> _cache = {};

  // One reused HTTP client (keeps the TLS connection warm across scans).
  static final http.Client _http = http.Client();

  // "Minimize thinking" generationConfig fragments, tried in order; the first the
  // model accepts is remembered for the session. Different Gemini generations use
  // different fields (3.x: thinkingLevel, 2.5: thinkingBudget), and the last entry
  // (null) is the fallback of letting it think if neither is accepted.
  static const List<Map<String, Object?>?> _thinkingCandidates = [
    {'thinkingLevel': 'low'},
    {'thinkingBudget': 0},
    null,
  ];
  static int _thinkingIdx = 0;

  /// When true, scans where Gemini and the on-device model strongly agree skip
  /// the Claude refine stage entirely (big speedup on easy scans). Kept OFF
  /// until the `[gate]` log below has been calibrated on a labelled eval set —
  /// the log prints what the gate WOULD do even while it's disabled.
  static const bool _gateClaudeBySonnet = false;

  /// Detects and classifies every object in [jpegBytes] for [config].
  ///
  /// [yolo] is the on-device model's result, run in parallel (it only feeds the
  /// Claude stage, never Gemini). It's awaited after the Gemini call returns, so
  /// the two run concurrently for free.
  Future<DetectionResult> detect(
    Uint8List jpegBytes,
    ScannerModelConfig config, {
    Future<DetectionResult?>? yolo,
  }) async {
    if (!AiConfig.hasKey) {
      throw LeafAnalysisException('No AI key configured.');
    }

    // Decode + orient + downscale off the UI isolate: on a multi-MP photo this
    // is heavy enough to stall the analysing spinner. Only the small shot bytes
    // and the frame dimensions come back — never the full-size image, which would
    // be an expensive copy across the isolate boundary.
    final (int frameW, int frameH, Uint8List shot) = await _runOffThread(() {
      final decoded = img.decodeImage(jpegBytes);
      if (decoded == null) {
        throw LeafAnalysisException('Could not read the captured photo.');
      }
      final up = img.bakeOrientation(decoded);
      return (up.width, up.height, _resizedJpeg(up, 1024));
    });
    final frameSize = Size(frameW.toDouble(), frameH.toDouble());

    final isPlant = config.id == 'plant';
    final classNames = isPlant
        ? [...leafClasses, ...pestClasses]
        : config.classNames;
    final objectNoun = isPlant
        ? 'pepper leaf or pest'
        : config.label.toLowerCase();

    final exemplars = await _exemplars(config.id);

    // REST parts: text + inline images. We call the REST endpoint directly (not
    // the google_generative_ai SDK) for two reasons the SDK can't give us: a
    // request timeout, and turning OFF Gemini's default "thinking" — the reason a
    // single detection call was taking 30-60s.
    final instruction = isPlant
        ? 'The photo below shows a black pepper plant. First decide, per object, '
              'whether it is a LEAF (disease) or a PEST, then give each object a '
              'bounding box (normalized 0-1000 as ymin,xmin,ymax,xmax) and the '
              'single best-matching class from: ${classNames.join(", ")}.'
        : config.id == 'berry'
        ? 'Now find and classify EVERY pepper spike in the photo below. '
              'Return one detection per spike with a bounding box (normalized '
              '0-1000 as ymin,xmin,ymax,xmax) and the best class from: '
              '${classNames.join(", ")}.\n'
              'Judge the berry set along the WHOLE spike, not the colour. A '
              'spike densely set with berries along its length is healthy_berry. '
              'A spike that is conspicuously sparse — long bare stretches of '
              'axis or only tiny aborted berry stubs over much of its body — is '
              'lace_bug_damage EVEN WHEN GREEN, as is any spike with brown/black '
              'feeding spots, scarring, or malformed/shrivelled/blackened '
              'berries. Minor natural unevenness on an otherwise well-filled '
              'spike is still healthy.\n$_berryHints'
        : 'Now find and classify EVERY $objectNoun object in the photo below. '
              'Return one detection per object with a bounding box (normalized '
              '0-1000 as ymin,xmin,ymax,xmax) and the best-matching class from: '
              '${classNames.join(", ")}.';

    final parts = <Map<String, Object?>>[
      {'text': 'Reference examples of each class:'},
      for (final e in exemplars) ...[
        {'text': 'Example — ${e.label}:'},
        {
          'inline_data': {
            'mime_type': 'image/jpeg',
            'data': base64Encode(e.bytes),
          },
        },
      ],
      {'text': instruction},
      {
        'inline_data': {'mime_type': 'image/jpeg', 'data': base64Encode(shot)},
      },
    ];

    final sw = Stopwatch()..start();
    final json = await _callGemini(classNames, parts);
    sw.stop();
    debugPrint(
      '[ai-detect] gemini ${sw.elapsedMilliseconds}ms '
      '(${exemplars.length} exemplars)',
    );

    // Resolve the parallel on-device result now (it ran during the Gemini call).
    final yoloResult = await (yolo ?? Future<DetectionResult?>.value(null));
    final yoloPriors = yoloResult?.detections ?? const <Detection>[];
    // Only treat priors as "agreement" when they met the strict YOLO bar — a
    // relaxed low-confidence second-pass result must never let Claude be skipped.
    final yoloTrusted = yoloResult != null && !yoloResult.lowConfidence;

    // Out-of-distribution gate: Gemini can be over-eager, flagging real pepper
    // photos that are just outside the training set. So we don't hard-drop on
    // is_relevant alone — we parse what it found first and decide below.
    final notRelevant = json['is_relevant'] == false;

    final list = (json['detections'] as List?) ?? const [];
    final dets = <Detection>[];
    for (final raw in list) {
      if (raw is! Map) continue;
      final label = (raw['label'] ?? '').toString();
      int classId = classNames.indexOf(label);
      if (classId < 0) classId = 0;
      final resolvedLabel = label.isEmpty ? classNames[classId] : label;
      final color = isPlant
          ? (_plantColors[resolvedLabel] ?? const Color(0xFFE67E22))
          : config.colorFor(classId);
      double n(Object? v) =>
          (v is num ? v.toDouble() : double.tryParse('${v ?? ''}') ?? 0) /
          1000.0;
      final l = n(raw['xmin']).clamp(0.0, 1.0);
      final t = n(raw['ymin']).clamp(0.0, 1.0);
      final r = n(raw['xmax']).clamp(0.0, 1.0);
      final b = n(raw['ymax']).clamp(0.0, 1.0);
      if (r <= l || b <= t) continue;
      final conf = raw['confidence'];
      dets.add(
        Detection(
          classId: classId,
          className: resolvedLabel,
          score: conf is num ? conf.toDouble() : 0.9,
          rect: Rect.fromLTRB(l, t, r, b),
          color: color,
        ),
      );
    }

    // If Gemini flagged the photo as not-pepper AND found nothing, don't just
    // show an empty screen — fall back to the on-device model's detections
    // (flagged low-confidence) so out-of-distribution images still predict.
    if (notRelevant && dets.isEmpty) {
      return DetectionResult(
        yoloPriors,
        frameSize,
        sw.elapsedMilliseconds,
        lowConfidence: yoloPriors.isNotEmpty,
      );
    }

    // Second stage: re-classify each detected crop with Claude for higher
    // fine-grained accuracy — but only the crops Gemini and the on-device model
    // DON'T already strongly agree on (when the gate is enabled). Any failure →
    // keep Gemini's labels.
    var result = dets;
    if (AiConfig.hasClaudeKey && dets.isNotEmpty) {
      final trusted = yoloTrusted && !notRelevant;
      // Crops the agreement rule would still send to Claude.
      final wouldSend = trusted
          ? dets.where((d) => !_agrees(d, yoloPriors)).toList()
          : dets;
      if (trusted) {
        debugPrint(
          '[gate] agreement would send ${wouldSend.length}/'
          '${dets.length} crops to Claude '
          '(gate ${_gateClaudeBySonnet ? "ON" : "OFF"})',
        );
      }
      final ambiguous = _gateClaudeBySonnet ? wouldSend : dets;
      if (ambiguous.isNotEmpty) {
        try {
          result = await _refineWithClaude(
            jpegBytes,
            dets,
            ambiguous,
            config,
            isPlant,
            classNames,
            exemplars,
            yoloPriors,
          );
        } catch (_) {
          result = dets;
        }
      }
    }

    return DetectionResult(result, frameSize, sw.elapsedMilliseconds);
  }

  /// True when Gemini and the on-device model agree strongly enough that the
  /// Claude refine stage can be skipped for [d]. The trustworthy signal is two
  /// independent models landing on the same class + box, not Gemini's own score.
  ///
  /// Always returns false (→ always refine) for: pests (the plant-mode YOLO is
  /// leaf-only and can't confirm a pest), Little Leaf (needs neighbour-size
  /// context a box can't verify), and uses a stricter bar for the Leaf Blight /
  /// Quick Wilt look-alike pair.
  static bool _agrees(Detection d, List<Detection> priors) {
    if (isPestClass(d.className) || d.className == 'Little Leaf') return false;
    final hard = d.className == 'Leaf Blight' || d.className == 'Quick Wilt';
    final minG = hard ? 0.95 : 0.90;
    final minY = hard ? 0.85 : 0.70;
    if (d.score < minG) return false;
    for (final p in priors) {
      if (p.className == d.className &&
          p.score >= minY &&
          _iou(d.rect, p.rect) >= 0.5) {
        return true;
      }
    }
    return false;
  }

  /// POSTs one detection request to the Gemini REST endpoint, with a hard timeout
  /// and thinking minimized. Returns the parsed JSON object. Throws
  /// [LeafAnalysisException] on any failure (the caller then falls back to YOLO).
  Future<Map<String, dynamic>> _callGemini(
    List<String> classNames,
    List<Map<String, Object?>> parts,
  ) async {
    final uri = Uri.parse(
      'https://generativelanguage.googleapis.com/v1beta/models/'
      '${AiConfig.model}:generateContent',
    );
    final body = <String, Object?>{
      'systemInstruction': {
        'parts': [
          {'text': _systemPrompt},
        ],
      },
      'contents': [
        {'role': 'user', 'parts': parts},
      ],
      'generationConfig': <String, Object?>{
        'temperature': 0.1,
        'maxOutputTokens': 2048,
        'responseMimeType': 'application/json',
        'responseSchema': _schema(classNames).toJson(),
      },
    };

    while (true) {
      final gc = body['generationConfig'] as Map<String, Object?>;
      final thinking = _thinkingCandidates[_thinkingIdx];
      if (thinking == null) {
        gc.remove('thinkingConfig');
      } else {
        gc['thinkingConfig'] = thinking;
      }

      final http.Response res;
      try {
        res = await _http
            .post(
              uri,
              headers: {
                'x-goog-api-key': AiConfig.apiKey,
                'Content-Type': 'application/json',
              },
              body: jsonEncode(body),
            )
            .timeout(const Duration(seconds: 25));
      } on Exception catch (e) {
        throw LeafAnalysisException('Gemini request failed: $e');
      }

      // If this Gemini generation rejects the thinking field, advance to the next
      // candidate and retry (once per candidate, remembered for the session).
      if (res.statusCode == 400 &&
          _thinkingIdx < _thinkingCandidates.length - 1 &&
          res.body.toLowerCase().contains('thinking')) {
        _thinkingIdx++;
        continue;
      }
      if (res.statusCode != 200) {
        throw LeafAnalysisException('Gemini ${res.statusCode}: ${res.body}');
      }

      final decoded = jsonDecode(utf8.decode(res.bodyBytes));
      final candidates =
          (decoded is Map ? decoded['candidates'] : null) as List?;
      final first = (candidates != null && candidates.isNotEmpty)
          ? candidates.first
          : null;
      final content = first is Map ? first['content'] : null;
      final cParts = content is Map ? content['parts'] : null;
      final firstPart = (cParts is List && cParts.isNotEmpty)
          ? cParts.first
          : null;
      final text = firstPart is Map ? firstPart['text'] as String? : null;
      if (text == null || text.trim().isEmpty) {
        throw LeafAnalysisException('Gemini returned no result.');
      }
      try {
        return jsonDecode(text.trim()) as Map<String, dynamic>;
      } catch (_) {
        throw LeafAnalysisException('Could not parse Gemini response.');
      }
    }
  }

  // ---- Claude crop refinement ----
  Future<List<Detection>> _refineWithClaude(
    Uint8List jpegBytes,
    List<Detection> dets,
    List<Detection> ambiguous,
    ScannerModelConfig config,
    bool isPlant,
    List<String> classNames,
    List<_Exemplar> exemplars,
    List<Detection> yoloPriors,
  ) async {
    const maxCrops = 12;
    // Only the ambiguous crops are sent; among those, classify the largest ones
    // and leave the rest on Gemini's labels (keeps the payload/latency bounded).
    final ordered = [...ambiguous]
      ..sort((a, b) => _area(b.rect).compareTo(_area(a.rect)));
    final chosen = ordered.take(maxCrops).toList();
    // ids are indices into the FULL [dets] list, so the merge loop keeps every
    // unsent detection on Gemini's label.
    final indexOf = {for (var i = 0; i < dets.length; i++) dets[i]: i};

    // Pick which boxes to crop and compute their priors on the main isolate
    // (cheap); do all the decode + crop + JPEG encoding off-thread.
    final selected = <(int, Rect)>[];
    final priors = <int, String>{};
    for (final d in chosen) {
      final id = indexOf[d]! + 1; // 1-based id shared with the prompt
      selected.add((id, d.rect));
      priors[id] = _priorFor(d.rect, yoloPriors);
    }

    final prepped = await _runOffThread(() {
      final decoded = img.decodeImage(jpegBytes);
      if (decoded == null) return null;
      final up = img.bakeOrientation(decoded);
      final cropsOut = <int, Uint8List>{};
      for (final (id, rect) in selected) {
        final c = _cropJpeg(up, rect, pad: 0.06, maxDim: 448);
        if (c != null) cropsOut[id] = c;
      }
      return (_resizedJpeg(up, 1024), cropsOut);
    });
    if (prepped == null) return dets;
    final (Uint8List overview, Map<int, Uint8List> cropBytes) = prepped;

    final crops = <ClaudeCrop>[];
    for (final (id, _) in selected) {
      final cb = cropBytes[id];
      if (cb != null) crops.add(ClaudeCrop(id, cb, prior: priors[id] ?? ''));
    }
    if (crops.isEmpty) return dets;

    // Plant domain asks two independent questions (disease + pest) so a leaf
    // with both is labeled for each; other domains ask a single class question.
    final aspects = isPlant
        ? const [_diseaseAspect, _pestAspect]
        : [
            ClaudeAspect(
              key: 'class',
              noun: config.label.toLowerCase(),
              classes: classNames,
              hints: _classHints(config.id),
            ),
          ];

    final results = await ClaudeClassifierService().classify(
      overviewJpeg: overview,
      crops: crops,
      exemplars: [
        for (final e in exemplars)
          ClaudeExemplar(e.label, e.bytes, note: _captions[e.label] ?? ''),
      ],
      aspects: aspects,
      objectNoun: isPlant ? 'pepper leaf' : config.label.toLowerCase(),
    );
    if (results.isEmpty) return dets;

    final out = <Detection>[];
    for (var i = 0; i < dets.length; i++) {
      final det = dets[i];
      final r = results[i + 1];
      if (r == null) {
        out.add(det); // not sent / no answer → keep Gemini label
        continue;
      }
      if (isPlant) {
        final disease = r['disease'];
        final pest = r['pest'];
        var added = false;
        if (disease != null && disease.isPositive) {
          out.add(_plantDet(det, disease.label, disease.confidence));
          added = true;
        }
        if (pest != null && pest.isPositive) {
          out.add(_plantDet(det, pest.label, pest.confidence));
          added = true;
        }
        if (!added) {
          // Only two explicit "None" verdicts establish a healthy leaf. A
          // missing/uncertain answer (including an unsupported positive label)
          // must abstain instead of silently becoming healthy or pest-free.
          final insufficientEvidence =
              disease == null ||
              pest == null ||
              disease.isUncertain ||
              pest.isUncertain;
          if (insufficientEvidence) continue;
          out.add(_plantDet(det, 'Healthy leaves', 0.9));
        }
      } else {
        final v = r['class'];
        if (v == null) {
          out.add(det);
          continue;
        }
        if (v.isUncertain) continue;
        // No asymmetric healthy floor here: it was double-counting the prompt's
        // healthy default and flipping genuinely-damaged (but borderline-scored)
        // green spikes to healthy. Balance now comes from the berry hints + the
        // cited-evidence gate in the Claude classifier.
        int classId = classNames.indexOf(v.label);
        if (classId < 0) classId = det.classId;
        out.add(
          Detection(
            classId: classId,
            className: v.label,
            score: v.confidence,
            rect: det.rect,
            color: config.colorFor(classId),
          ),
        );
      }
    }
    return out;
  }

  // Builds a plant-domain detection (leaf disease or pest) for [det]'s box.
  Detection _plantDet(Detection det, String label, double conf) {
    final all = [...leafClasses, ...pestClasses];
    int classId = all.indexOf(label);
    if (classId < 0) classId = det.classId;
    return Detection(
      classId: classId,
      className: label,
      score: conf,
      rect: det.rect,
      color: _plantColors[label] ?? const Color(0xFFE67E22),
    );
  }

  /// Pre-loads and caches the reference exemplars for [domainId] so the first
  /// scan doesn't pay the decode cost. Safe to call un-awaited and repeatedly.
  static Future<void> warmUp(String domainId) =>
      AiDetectionService()._exemplars(domainId).then((_) {}, onError: (_) {});

  static const _diseaseAspect = ClaudeAspect(
    key: 'disease',
    noun: 'leaf disease',
    classes: ['Leaf Blight', 'Little Leaf', 'Quick Wilt'],
    hints: _diseaseHints,
  );
  static const _pestAspect = ClaudeAspect(
    key: 'pest',
    noun: 'pest or pest damage',
    classes: [
      'Diconocoris distanti',
      'Gynaikothrips karny',
      'Pterolopha annulata',
    ],
    hints: _pestHints,
  );

  static double _area(Rect r) => r.width * r.height;

  // Best-overlapping trained-model detection for [rect], as a short hint string
  // ("local model: Leaf Blight 0.82"), or '' if nothing overlaps enough.
  static String _priorFor(Rect rect, List<Detection> priors) {
    Detection? best;
    var bestIou = 0.30; // require a meaningful overlap
    for (final p in priors) {
      final i = _iou(rect, p.rect);
      if (i > bestIou) {
        bestIou = i;
        best = p;
      }
    }
    if (best == null) return '';
    return 'local model: ${best.className} '
        '${(best.score.clamp(0.0, 1.0) * 100).round()}%';
  }

  static double _iou(Rect a, Rect b) {
    final x1 = a.left > b.left ? a.left : b.left;
    final y1 = a.top > b.top ? a.top : b.top;
    final x2 = a.right < b.right ? a.right : b.right;
    final y2 = a.bottom < b.bottom ? a.bottom : b.bottom;
    final iw = x2 - x1, ih = y2 - y1;
    if (iw <= 0 || ih <= 0) return 0;
    final inter = iw * ih;
    final union = _area(a) + _area(b) - inter;
    return union <= 0 ? 0 : inter / union;
  }

  // Crops [rect] (normalized 0..1) from [src] with a little padding and returns
  // a resized JPEG, or null if the region is degenerate.
  static Uint8List? _cropJpeg(
    img.Image src,
    Rect rect, {
    double pad = 0.06,
    int maxDim = 448,
  }) {
    final w = src.width, h = src.height;
    final l = ((rect.left - pad) * w).clamp(0, w - 1).round();
    final t = ((rect.top - pad) * h).clamp(0, h - 1).round();
    final r = ((rect.right + pad) * w).clamp(1, w).round();
    final b = ((rect.bottom + pad) * h).clamp(1, h).round();
    final cw = r - l, ch = b - t;
    if (cw < 8 || ch < 8) return null;
    final cropped = img.copyCrop(src, x: l, y: t, width: cw, height: ch);
    return _resizedJpeg(cropped, maxDim);
  }

  // ---- reference exemplars ----
  Future<List<_Exemplar>> _exemplars(String domainId) async {
    if (_cache.containsKey(domainId)) return _cache[domainId]!;
    final spec = _refs[domainId] ?? const [];
    final manifest = await AssetManifest.loadFromAssetBundle(rootBundle);
    final assets = manifest.listAssets();

    // Exemplars per class, by domain — more look-alikes grounds subtle calls
    // (Quick Wilt vs Leaf Blight, the three pest classes). These blocks are
    // prompt-cached by the Claude classifier, so the extra images are paid for
    // once per domain. The combined 'plant' scanner has 8 classes, so it's
    // capped at 10 (80 imgs) to stay under Claude's 100-image/request limit once
    // the overview + up to maxCrops object crops are added. Berry is unchanged.
    final perClass = _exemplarLimit(domainId);

    // Load the raw asset bytes on the main isolate (rootBundle needs it, and the
    // IO is light), but decode + bake + re-encode every image — the heavy part,
    // up to 80 images for the plant domain — off-thread.
    final raw = <(String, Uint8List)>[];
    for (final entry in spec) {
      final label = entry[0];
      final folder = entry[1];
      final matches =
          assets.where((a) => a.startsWith(folder) && _isImage(a)).toList()
            ..sort();
      for (final match in matches.take(perClass)) {
        final data = await rootBundle.load(match);
        raw.add((label, data.buffer.asUint8List()));
      }
    }

    final out = await _runOffThread(() {
      final list = <_Exemplar>[];
      for (final (label, bytes) in raw) {
        final decoded = img.decodeImage(bytes);
        if (decoded == null) continue;
        list.add(
          _Exemplar(label, _resizedJpeg(img.bakeOrientation(decoded), 384)),
        );
      }
      return list;
    });
    _cache[domainId] = out;
    return out;
  }

  static int _exemplarLimit(String domainId) => switch (domainId) {
    'plant' => 10, // 8 classes × 10 = 80, + overview + crops < 100
    'berry' => 6,
    _ => 15, // standalone leaf / pest (4 classes each)
  };

  static bool _isImage(String a) {
    final l = a.toLowerCase();
    return l.endsWith('.jpg') || l.endsWith('.jpeg') || l.endsWith('.png');
  }

  static Uint8List _resizedJpeg(img.Image src, int maxDim) {
    final longest = src.width > src.height ? src.width : src.height;
    final scaled = longest > maxDim
        ? img.copyResize(
            src,
            width: src.width >= src.height ? maxDim : null,
            height: src.height > src.width ? maxDim : null,
          )
        : src;
    return Uint8List.fromList(img.encodeJpg(scaled, quality: 85));
  }

  static const String _systemPrompt = '''
You are a plant vision system for black pepper. You are shown labeled reference
photos of each class, then a target photo.

First decide if the target photo actually shows the expected black pepper part
(leaf, berry cluster, or pest on a pepper plant). If it does NOT — a different
plant, an animal, a person, an object, or an unclear/blank image — set
is_relevant to false and return an empty detections list. Never classify a
non-pepper subject.

If it is relevant, set is_relevant to true and detect EVERY matching object
(there may be several — classify all of them), giving each a tight bounding box
and the single best-matching class from the allowed list.

Default to Healthy leaves. Assign a disease class ONLY when a clear, nameable
disease sign is visible on the leaf blade; otherwise the leaf is Healthy. A
mostly-green, firm leaf with just a little tip/edge browning, or one or two tiny
specks, is HEALTHY — not a disease.

Run this checklist per leaf and pick the FIRST that clearly matches:
1. Leaf Blight: the blade carries distinct SPOTS / DOTS scattered ON the leaf
   surface (two or more). The spots are very characteristic — dark brown/black with
   a JAGGED, STAR-SHAPED or radiating fimbriate margin, often with a PALE grey/tan/
   white CENTRE (a "fish-eye" or target look), and usually a yellow halo around
   them. These star-shaped pale-centred spots are the signature of Leaf Blight and
   NEVER appear in Quick Wilt. If you can point to such spots on the blade, it is
   Leaf Blight — EVEN IF the leaf tip or edge is ALSO browned/dead. A blighted leaf
   very often has a dead tip as well; the spots on the blade still make it Leaf
   Blight. (A single tiny speck only → Healthy.)
2. Quick Wilt: NO distinct spots anywhere on the blade; instead the leaf EDGE, TIP
   or MARGIN is darkening into a CONTINUOUS brown/grey dead zone that spreads inward
   (often with a darker edge line and a yellow band next to the green). Darkened
   edges / a solid dead tip-or-margin patch AND a clean, spot-free blade = Quick
   Wilt. Yellowing, drooping or wilting may be present but is NOT required. If the
   blade shows the star-shaped / pale-centred spots above, it is Leaf Blight, NOT
   Quick Wilt, even when the tip is dead. (A paper-thin dry rim only at the very
   tip, nothing else, is still Healthy.)
3. Little Leaf: a leaf clearly SMALLER / narrower / crinkled / cupped than the
   mature leaves AROUND it. Requires other leaves to compare against — if only one
   leaf is visible it can NEVER be Little Leaf.
4. Otherwise: Healthy leaves.
For PESTS (combined leaf+pest scans) choose a pest class ONLY when a live insect
OR its specific feeding sign is visible; match the pest reference photos:
- Diconocoris distanti (pepper lace bug, sucking): fine PALE/whitish stippling or
  chlorotic flecking on the leaf, tiny dark shiny "varnish" excrement specks
  beneath, and/or flower spikes & young berries that blacken, grey and dry.
- Gynaikothrips karny (gall/leaf thrips, rasping-sucking): leaves CURL, FOLD or
  ROLL (along the midrib/margins) into galls, with silvery/bronzed stippling and
  brown-to-reddish scarring and tiny black fecal specks in the folds.
- Pterolopha annulata (leaf-webbing/folding caterpillar, chewing): two or more
  leaves WEBBED or FOLDED together and dried brown into a pod/shelter, hanging
  dead among healthy green leaves, with shrivelled leaves and blackened/dried
  berry spikes; silk webbing, a banded caterpillar, skeletonized "window" patches
  or frass may also show.
No stippling, no curling/galls, no webbed/dried folded leaves, no dark feeding
specks, no visible insect → no pest (Healthy). Pick a pest class only if its own
sign is present.

Leaf Blight vs Quick Wilt (the most common confusion) — DECISIVE TEST: look for
distinct SPOTS/DOTS on the blade, especially dark spots with a jagged/star-shaped
margin and a pale centre. If such spots are present anywhere on the leaf → Leaf
Blight. If there are NO such spots and the only damage is a darkened continuous
EDGE / TIP / MARGIN dead zone → Quick Wilt. Put plainly: SPOTS (star-shaped, pale-
centred) = Leaf Blight; DARKENED EDGES WITH A SPOT-FREE BLADE = Quick Wilt. This
test wins over colour and how much brown there is. IMPORTANT: a Leaf-Blight leaf
OFTEN ALSO has a dead/darkened tip — a dead tip does NOT make it Quick Wilt. The
spots decide: spots anywhere → Leaf Blight even with a dead tip; a dead edge/tip
with a clean spot-free blade → Quick Wilt. Weight the reference photos of each class
heavily, but IGNORE their backgrounds: some healthy references are on a plain grey
studio backdrop and the diseased ones are field photos — background, lighting and
photo style are NEVER a disease cue.
A photo usually contains MANY leaves — return a SEPARATE detection (its own box
and class) for EVERY distinct leaf you can see, including partially visible,
background and overlapping ones. Do not merge several leaves into one box and do
not report only the main/front leaf; aim to cover them all.

A single leaf can also have BOTH a disease and pest damage — return a separate
detection for each. Match reference symptoms carefully; do not guess. Return
only the structured result.
''';

  // Single-class cues for non-plant domains (berry). The combined leaf+pest
  // domain uses _diseaseHints / _pestHints via its two aspects instead.
  static String _classHints(String domainId) {
    if (domainId == 'berry') return _berryHints;
    return '';
  }

  static const String _berryHints = '''
Judge the WHOLE spike from base to tip, and judge the BERRY SET, not the colour
(green spikes can be either healthy or damaged).
- healthy_berry: berries are set CONTINUOUSLY and fairly DENSELY along MOST of the
  spike's length — plump and rounded. Minor natural unevenness is fine: slightly
  irregular spacing, mixed maturity, a small gap, and a naturally tapering tip
  with a few berries all still count as healthy, AS LONG AS the spike is mostly
  filled with berries.
- lace_bug_damage: call this when ANY of these is present:
    * a CONSPICUOUSLY SPARSE / GAPPY set — long bare stretches of axis, or large
      sections carrying only tiny ABORTED berry stubs instead of berries. A
      healthy spike is packed along its length; a spike that is bare or stub-only
      over much of its body is damaged, EVEN WHEN GREEN;
    * distinct brown/black feeding spots, stippling or scarring ON the berries;
    * berries clearly malformed, shrivelled, flattened, or blackened/dried.
Tie-breaker: a spike densely set with berries along its length = healthy_berry.
A spike where much of the axis is bare or carries only aborted stubs, or that
shows feeding spots / shrivelled / blackened berries = lace_bug_damage. A short
naturally tapering tip is not damage on its own, but a long bare mid-section or
many aborted/missing berries IS.''';

  static const String _diseaseHints = '''
Compare the crop feature-by-feature to the labeled reference photos of each class
(there are several per class). Decide by running this checklist, and name what you
found in "evidence":
- Leaf Blight: the blade carries distinct SPOTS / DOTS scattered ON the leaf
  surface (two or more). Characteristic look: dark brown/black spots with a JAGGED,
  STAR-SHAPED or radiating fimbriate margin and often a PALE grey/tan/white CENTRE
  (fish-eye / target spots), usually ringed by a yellow halo. These star-shaped
  pale-centred spots are the signature of Leaf Blight and NEVER appear in Quick
  Wilt. If such spots are on the blade it is Leaf Blight — EVEN IF the tip/edge is
  ALSO browned or dead (a blighted leaf often has a dead tip too; the spots still
  decide). "evidence" must name the spots (e.g. "~10 dark star-shaped spots with
  pale centres across the blade, plus a dead tip").
- Quick Wilt: NO distinct spots anywhere on the blade; instead the leaf EDGE, TIP
  or MARGIN is darkened into a CONTINUOUS brown/grey dead zone that spreads inward,
  usually with a darker edge line and a yellow band next to the green. A darkened
  edge / solid dead tip-or-margin patch together with a CLEAN, SPOT-FREE blade =
  Quick Wilt. Yellowing, drooping or wilting MAY be present but is NOT required. If
  the blade shows the star-shaped / pale-centred spots above, it is Leaf Blight, not
  Quick Wilt. "evidence" must name the darkened edge/tip dead zone AND that the rest
  of the blade is spot-free (e.g. "leaf tip browned into one connected dead patch
  with a dark line, no spots anywhere on the blade").
- Little Leaf: judged by SIZE/SHAPE — clearly smaller, narrower, crinkled/cupped or
  deformed versus the mature leaves around it. Compare against neighbouring leaves
  in the context photo first.
  HARD RULE: if the photo shows only ONE leaf (nothing to compare against), it can
  NEVER be Little Leaf — answer None instead.
- None (Healthy) — the DEFAULT: answer None unless a sign above is clearly met. A
  firm green leaf with only a paper-thin dry tip rim, a single tiny speck, or faint
  yellowing and nothing else is None, NOT a disease. No distinct spots AND no
  darkened edge/tip dead zone → None.
Tie-breakers:
- Leaf Blight vs Quick Wilt — DECISIVE: distinct SPOTS/DOTS scattered on the blade
  = Leaf Blight; NO spots but a darkened CONTINUOUS edge/tip/margin dead zone =
  Quick Wilt. SPOTS = Blight; DARKENED EDGES WITHOUT SPOTS = Quick Wilt. This wins
  over colour, amount of brown, and whether wilting shows. A leaf with spots is
  never Quick Wilt; a leaf whose only damage is a darkened edge/tip zone with no
  spots is never Leaf Blight.
- Little Leaf vs None: a leaf clearly smaller than its neighbours (with crinkling/
  deformity) = Little Leaf; a full-sized leaf, or a LONE leaf with nothing to
  compare against, = None (never Little Leaf on a single leaf).
IGNORE background, lighting and photo style: some reference leaves sit on a plain
grey studio backdrop and others are field shots — backdrop is never a disease sign.
Your "evidence" must name a feature ON THE BLADE; a plain/studio background, good
lighting, or "looks like the reference" is NOT evidence.''';

  static const String _pestHints = '''
Compare the crop feature-by-feature to the labeled pest reference photos (there are
several per class). A leaf can show pest damage with NO visible insect — judge by
the damage type. Name what you found in "evidence":
- Diconocoris distanti (pepper lace bug — SUCKING): fine PALE / whitish stippling
  or chlorotic flecking on the leaf, with tiny dark shiny "varnish" excrement specks
  on the underside; on flower spikes / young berries a brown-to-black discoloration
  with greying, wilting and drying spikes that drop (empty seeds). The insect is
  small and flat with lacy net-veined wings; nymphs are dark and spiny. "evidence"
  names the stippling / underside specks / blackened spike.
- Gynaikothrips karny (gall / leaf thrips — rasping-sucking): leaves CURL, FOLD or
  ROLL (usually along the midrib or margins) into galls/pockets; silvery or bronzed
  stippling with brown/reddish/purplish scarring, often tiny black fecal specks
  inside the folds; foliage distorted and discoloured. The thrips are minute,
  slender, dark. "evidence" names the curl/fold/gall + silvery scarring.
- Pterolopha annulata (leaf-webbing / folding CATERPILLAR — chewing): two or more
  leaves WEBBED or FOLDED together and dried brown into a pod/shelter, hanging dead
  among healthy green leaves; shrivelled dried leaves and blackened/dried berry
  spikes; silk webbing, a banded caterpillar, skeletonized "window" patches, chewed
  holes or frass may also be present. "evidence" names the webbed/folded dried
  leaves / tied pod / blackened spike / window / frass.
- None: no insect and no feeding sign — no stippling, no underside specks, no
  curling/folding/galls, no silvery scarring, no webbed/dried folded leaves, no
  windows/holes and no blackened spikes. This is the DEFAULT.
Damage type tells them apart: pale stippling + dark underside specks or blackened
spikes = lace bug; curling/folding, galls and silvery scarring = thrips; leaves
webbed/folded together and dried into pods (with blackened spikes/windows/frass) =
the caterpillar. IGNORE background, lighting and photo style — "evidence" must name
a feature ON the leaf/spike itself, never the backdrop.''';

  // Short distinguishing notes attached to each reference exemplar image.
  static const Map<String, String> _captions = {
    'Leaf Blight':
        'distinct SPOTS/DOTS on the blade — dark star-shaped/jagged-edged '
        'spots with pale grey/tan centres (fish-eye) and yellow halos. Spots = Leaf '
        'Blight, even if the tip is ALSO dead; Quick Wilt never has these spots',
    'Quick Wilt':
        'NO spots — the EDGE/TIP/MARGIN darkened into one continuous '
        'brown/grey dead zone spreading inward (dark edge line + yellow band); '
        'darkened edges without spots = Quick Wilt (wilting not required)',
    'Little Leaf':
        'leaf clearly smaller/narrower/crinkled vs the mature leaves '
        'around it — needs neighbours to compare, never on a lone leaf',
    'Healthy leaves':
        'firm uniform green, no 3+ spots and no spreading dead patch; '
        'shown here on a plain grey studio backdrop — judge the LEAF, not the '
        'background',
    'Diconocoris distanti':
        'pepper lace bug (sucking); pale stippling on the leaf '
        'with dark shiny excrement specks beneath, and/or flower spikes that '
        'blacken, grey and dry; flat lace/net-winged bug',
    'Gynaikothrips karny':
        'gall/leaf thrips (rasping-sucking); leaves curl/fold/'
        'roll into galls with silvery-bronze scarring and tiny black fecal specks '
        'in the folds',
    'Pterolopha annulata':
        'leaf-webbing/folding caterpillar (chewing); two+ leaves '
        'webbed/folded together and dried brown into a pod, hanging dead among '
        'green leaves, with blackened/dried spikes; silk, banded larva or window '
        'patches may show',
    'healthy':
        'no insect and no feeding sign — no stippling, curling/galls, '
        'webbed/dried folded leaves, windows or dark feeding specks',
    'lace_bug_damage':
        'sparse spike with long bare axis / aborted berry stubs, '
        'OR feeding spots / malformed / shrivelled berries — incl. GREEN spikes',
    'healthy_berry':
        'berries set densely along the length of the spike, plump '
        'and rounded (minor natural unevenness is still healthy)',
  };

  static Schema _schema(List<String> classNames) => Schema.object(
    properties: {
      'is_relevant': Schema.boolean(),
      'detections': Schema.array(
        items: Schema.object(
          properties: {
            'label': Schema.enumString(enumValues: classNames),
            'confidence': Schema.number(),
            'ymin': Schema.number(),
            'xmin': Schema.number(),
            'ymax': Schema.number(),
            'xmax': Schema.number(),
          },
          requiredProperties: [
            'label',
            'confidence',
            'ymin',
            'xmin',
            'ymax',
            'xmax',
          ],
        ),
      ),
    },
    requiredProperties: ['is_relevant', 'detections'],
  );
}

class _Exemplar {
  final String label;
  final Uint8List bytes;
  _Exemplar(this.label, this.bytes);
}
