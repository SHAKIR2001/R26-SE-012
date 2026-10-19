import 'dart:convert';
import 'dart:typed_data';

import 'package:anthropic_sdk_dart/anthropic_sdk_dart.dart';
import 'package:flutter/foundation.dart' show visibleForTesting;

import 'ai_config.dart';

/// One cropped object to classify, tagged with a stable id. [prior] is an
/// optional hint from the on-device trained model (e.g. "local model: Leaf
/// Blight 0.82") shown to Claude alongside the crop.
class ClaudeCrop {
  final int id;
  final Uint8List jpeg;
  final String prior;
  const ClaudeCrop(this.id, this.jpeg, {this.prior = ''});
}

/// A labeled reference exemplar (one representative photo per class), optionally
/// annotated with the feature that distinguishes it from its look-alikes.
class ClaudeExemplar {
  final String label;
  final Uint8List jpeg;
  final String note;
  const ClaudeExemplar(this.label, this.jpeg, {this.note = ''});
}

/// One question asked about every crop. Single-label domains use one aspect
/// (e.g. 'class'); the combined leaf+pest domain uses two ('disease' + 'pest')
/// so a leaf that has BOTH is labeled for each independently instead of being
/// forced into a single tied guess.
class ClaudeAspect {
  final String key; // JSON key, e.g. 'disease'
  final String noun; // human phrasing, e.g. 'leaf disease'
  final List<String> classes; // allowed positive labels
  final String hints; // distinguishing cues
  const ClaudeAspect({
    required this.key,
    required this.noun,
    required this.classes,
    this.hints = '',
  });
}

/// Claude's verdict for one aspect of one crop.
class ClaudeVerdict {
  final String label; // a class, or 'None', or 'Uncertain'
  final double confidence; // 0..1
  const ClaudeVerdict(this.label, this.confidence);

  bool get isNone => label.toLowerCase() == 'none';
  bool get isUncertain => label.toLowerCase() == 'uncertain';
  bool get isPositive => !isNone && !isUncertain;
}

/// Second-stage classifier. Given the full photo for context, individual object
/// crops, and annotated per-class reference exemplars, Claude (with extended
/// thinking) answers each [ClaudeAspect] per crop — or abstains with 'None' /
/// 'Uncertain'. Reference blocks are prompt-cached so repeated scans in a domain
/// only pay for them once.
///
/// Returns crop id -> (aspect key -> verdict). Any thrown error is treated by
/// the caller as "keep the Gemini labels".
class ClaudeClassifierService {
  // One reused client → no fresh TLS handshake per scan.
  static final AnthropicClient _client = AnthropicClient(
    config: const AnthropicConfig(
      authProvider: ApiKeyProvider(AiConfig.claudeApiKey),
    ),
  );

  Future<Map<int, Map<String, ClaudeVerdict>>> classify({
    required Uint8List overviewJpeg,
    required List<ClaudeCrop> crops,
    required List<ClaudeExemplar> exemplars,
    required List<ClaudeAspect> aspects,
    required String objectNoun,
  }) async {
    if (!AiConfig.hasClaudeKey || crops.isEmpty || aspects.isEmpty) {
      return const {};
    }

    final blocks = <InputContentBlock>[
      InputContentBlock.text(
        'You are grading a black pepper plant. Below are ANNOTATED reference '
        'photos of each class, then the full photo for context, then individual '
        'cropped objects numbered by id. Study the references and their notes '
        'feature-by-feature before deciding.',
      ),
      InputContentBlock.text('Reference examples:'),
    ];
    // Reference exemplars are identical every call → cache them. Marking the
    // LAST exemplar image caches the whole prefix up to that point.
    for (var i = 0; i < exemplars.length; i++) {
      final e = exemplars[i];
      final isLast = i == exemplars.length - 1;
      blocks.add(
        InputContentBlock.text(
          'Reference — ${e.label}${e.note.isEmpty ? '' : ': ${e.note}'}',
        ),
      );
      blocks.add(
        InputContentBlock.image(
          ImageSource.base64(
            mediaType: ImageMediaType.jpeg,
            data: base64Encode(e.jpeg),
          ),
          cacheControl: isLast ? const CacheControlEphemeral() : null,
        ),
      );
    }
    blocks.add(
      InputContentBlock.text(
        'Full photo for CONTEXT — do not classify it directly, but DO use it to '
        'judge each crop\'s size and shape relative to the leaves around it. A leaf '
        'clearly smaller than its neighbours here is a strong Little Leaf signal; '
        'but if this photo shows only ONE leaf with nothing to compare against, no '
        'crop can be Little Leaf:',
      ),
    );
    blocks.add(_img(overviewJpeg));
    blocks.add(
      InputContentBlock.text(
        'Now assess each cropped $objectNoun below. Each crop is one object.',
      ),
    );
    for (final c in crops) {
      blocks.add(
        InputContentBlock.text(
          'Object id ${c.id}${c.prior.isEmpty ? '' : ' — ${c.prior}'}:',
        ),
      );
      blocks.add(_img(c.jpeg));
    }
    blocks.add(InputContentBlock.text(_instruction(aspects)));

    final res = await _client.messages
        .create(
          MessageCreateRequest(
            model: AiConfig.claudeModel,
            maxTokens: 6000,
            // No `thinking` param: Opus 5.5 / Sonnet 5.5 REJECT the old
            // ThinkingConfig.enabled(budgetTokens:) with a 400 ("use adaptive"),
            // which silently dropped every crop back to the Gemini label. Omitting
            // it runs adaptive thinking by default on these models — so Claude
            // actually reasons about the crop before committing.
            messages: [InputMessage.userBlocks(blocks)],
          ),
        )
        .timeout(const Duration(seconds: 20));
    return _parse(res.text, aspects);
  }

  static InputContentBlock _img(Uint8List jpeg) => InputContentBlock.image(
    ImageSource.base64(
      mediaType: ImageMediaType.jpeg,
      data: base64Encode(jpeg),
    ),
  );

  static String _instruction(List<ClaudeAspect> aspects) {
    final b = StringBuffer()
      ..writeln('For EACH object id, answer every question below:');
    for (final a in aspects) {
      b.writeln(
        '- "${a.key}": which ${a.noun} is present? Choose ONE of '
        '[${a.classes.join(", ")}], or "None" if this object shows no '
        '${a.noun}.',
      );
      if (a.hints.isNotEmpty) b.writeln('  cues:\n${_indent(a.hints)}');
    }
    b
      ..writeln()
      ..writeln(
        'An object can be positive for MORE THAN ONE question (e.g. a '
        'leaf may have both a disease AND pest damage) — answer each question '
        'independently. Use "Uncertain" only if you genuinely cannot tell.',
      )
      ..writeln(
        'Match against the reference photos, not prior assumptions; '
        'judge each crop on its own.',
      )
      ..writeln(
        'Some objects include a suggestion from an on-device model '
        'trained on these exact classes ("local model: ..."). Treat it as a '
        'STRONG hint and lean toward it when the crop is ambiguous, but '
        'override it if the crop and reference photos clearly disagree.',
      )
      ..writeln()
      ..writeln(
        'For each answer, "evidence" MUST name the SPECIFIC visible '
        'feature that justifies the label (e.g. "brown feeding spots on two '
        'berries"), or "none" if you saw no positive sign. If "evidence" is '
        'empty or "none", you did NOT find a positive sign — then the label '
        'MUST be the healthy/None option, never a disease, pest or damage '
        'class.',
      )
      ..writeln()
      ..writeln(
        'Healthy/None is the DEFAULT for every question. Leave it ONLY '
        'when a specific sign clearly meets a cue above. For DISEASE: distinct '
        'spots/dots scattered on the blade (Leaf Blight), a darkened continuous '
        'edge/tip/margin dead zone with NO spots (Quick Wilt), or a leaf plainly '
        'smaller than its neighbours (Little Leaf). For PESTS: pale stippling with dark '
        'underside specks or blackened spikes (lace bug), curled/folded/galled '
        'leaves with silvery scarring (thrips), or leaves webbed/folded together '
        'and dried into pods with blackened spikes/windows (caterpillar). A firm '
        'flat green leaf with just a thin dry tip, one or two specks, or faint '
        'yellowing — and no pest sign — is Healthy/None, not a disease or pest.',
      )
      ..writeln(
        'IGNORE background, lighting and photo style: some reference '
        'leaves sit on a plain grey studio backdrop while diseased/infested ones '
        'are field photos. Backdrop, blur, shadows and colour cast are NEVER '
        'evidence — "evidence" must name a feature ON the object itself (a spot, '
        'patch, stipple, gall, web, hole or insect you can point to).',
      )
      ..writeln()
      ..writeln(
        'Respond with ONLY a JSON object, no prose, no markdown fences:',
      );
    final shape = aspects
        .map(
          (a) =>
              '"${a.key}":{"label":"<class or None>","confidence":0.0,'
              '"evidence":"<specific visible feature, or none>"}',
        )
        .join(',');
    b.writeln('{"results":[{"id":1,$shape}]}');
    return b.toString();
  }

  static String _indent(String s) =>
      s.split('\n').map((l) => '    $l').join('\n');

  static Map<int, Map<String, ClaudeVerdict>> _parse(
    String? text,
    List<ClaudeAspect> aspects,
  ) {
    if (text == null || text.trim().isEmpty) return const {};
    var t = text.trim();
    if (t.startsWith('```')) {
      t = t.replaceFirst(RegExp(r'^```[a-zA-Z]*\n?'), '');
      if (t.endsWith('```')) t = t.substring(0, t.length - 3);
      t = t.trim();
    }
    Map<String, dynamic> json;
    try {
      json = jsonDecode(t) as Map<String, dynamic>;
    } catch (_) {
      return const {};
    }
    final list = (json['results'] as List?) ?? const [];
    // Per-aspect case-insensitive class lookup.
    final lookups = {
      for (final a in aspects)
        a.key: {for (final c in a.classes) c.toLowerCase(): c},
    };
    final out = <int, Map<String, ClaudeVerdict>>{};
    for (final raw in list) {
      if (raw is! Map) continue;
      final id = raw['id'];
      if (id is! num) continue;
      final perAspect = <String, ClaudeVerdict>{};
      for (final a in aspects) {
        final cell = raw[a.key];
        if (cell is! Map) continue;
        final rawLabel = (cell['label'] ?? '').toString().trim();
        final low = rawLabel.toLowerCase();
        var label =
            lookups[a.key]![low] ??
            (low == 'none'
                ? 'None'
                : low == 'uncertain'
                ? 'Uncertain'
                : rawLabel);
        // Positive-evidence gate: a disease/pest/damage label without specific
        // cited evidence is uncertain. It must not silently become healthy.
        final evidence = (cell['evidence'] ?? '')
            .toString()
            .trim()
            .toLowerCase();
        final hasEvidence = evidence.isNotEmpty && evidence != 'none';
        final isPositive =
            label != 'None' &&
            label != 'Uncertain' &&
            lookups[a.key]!.containsValue(label);
        if (isPositive && !hasEvidence) label = 'Uncertain';
        final conf = cell['confidence'];
        perAspect[a.key] = ClaudeVerdict(
          label,
          conf is num ? conf.toDouble().clamp(0.0, 1.0) : 0.8,
        );
      }
      if (perAspect.isNotEmpty) out[id.toInt()] = perAspect;
    }
    return out;
  }

  @visibleForTesting
  static Map<int, Map<String, ClaudeVerdict>> parseForTesting(
    String text,
    List<ClaudeAspect> aspects,
  ) => _parse(text, aspects);
}
