import 'dart:convert';
import 'dart:typed_data';

import 'package:google_generative_ai/google_generative_ai.dart';

import '../../core/locale/app_locale.dart';
import 'berry_analysis.dart';
import 'ai_config.dart';
import 'ai_leaf_service.dart' show LeafAnalysisException;

/// Sends a pepper-berry cluster photo to AI for the *vision* task only:
/// judge damage severity visually, name the problem. Treatment is intentionally
/// NOT requested — the app's [RemediationEngine] owns that so an LLM can never
/// suggest an export-banned chemical.
class AiBerryService {
  static const List<String> _problemVocab = [
    'Healthy',
    'Lace bug damage',
    'Other damage',
    'Uncertain',
  ];

  late final GenerativeModel _model = GenerativeModel(
    model: AiConfig.model,
    apiKey: AiConfig.apiKey,
    systemInstruction: Content.system(_systemPrompt),
    generationConfig: GenerationConfig(
      temperature: 0.2,
      responseMimeType: 'application/json',
      responseSchema: _schema,
    ),
  );

  Future<BerryAnalysis> analyze(Uint8List jpegBytes) async {
    if (!AiConfig.hasKey) {
      throw LeafAnalysisException(
        'No AI API key. Run with --dart-define=GEMINI_API_KEY=your_key',
      );
    }

    final GenerateContentResponse res;
    try {
      res = await _model.generateContent([
        Content.multi([
          TextPart(
            '$_taskPrompt\n\nWrite summary and affected_regions in '
            '${currentPromptLanguage()}. Keep problem_type exactly as the '
            'allowed English values.',
          ),
          DataPart('image/jpeg', jpegBytes),
        ]),
      ]);
    } on Exception catch (e) {
      throw LeafAnalysisException('AI request failed: $e');
    }

    final text = res.text?.trim();
    if (text == null || text.isEmpty) {
      throw LeafAnalysisException('AI returned no result.');
    }
    try {
      return BerryAnalysis.fromJson(jsonDecode(text) as Map<String, dynamic>);
    } catch (_) {
      throw LeafAnalysisException('Could not parse AI response:\n$text');
    }
  }

  static const String _systemPrompt = '''
You are an expert agronomist grading black pepper (Piper nigrum) berries for
export quality. A pepper "berry" is a SPIKE (spadix) carrying many individual
berry-seeds (peppercorns) along its length. You look at ONE close-up photo of a
spike and report what you can see.

Rules:
- First decide if the image is really a pepper berry spike. If not (leaves only,
  a hand, another plant, too blurry/dark), set is_berry_cluster to false and do
  not invent a severity.
- Judge damage SEVERITY visually: estimate, as a percentage 0-100, how much of
  the spike overall looks affected — the proportion of berries/spike showing
  damage weighted by how bad it is. A spike where most berries are blackened or
  shrivelled is high (e.g. 80-100); a few faint marks is low (e.g. 10-20); a
  clean spike is 0. Base it on what you actually see, not a fixed rule.
- Lace bug damage shows as pale stippling, bronzing, blackening, shrivelling or
  scarring — but ALSO on GREEN, immature spikes as an uneven/gappy/sparse berry
  set, missing or aborted berries, and malformed/undersized berries. Do NOT treat
  a green spike as healthy: judge the berry set and shape, not just colour. A
  healthy spike is densely and evenly packed with plump, uniform berries.
  Choose problem_type from the allowed list only.
- DO NOT recommend any pesticide, chemical, brand or dosage. Treatment is
  handled by the application, not you. Only describe what you observe.
- Be honest about confidence; a single photo has limits.
''';

  static const String _taskPrompt =
      'Grade this black pepper berry spike. Judge how damaged it looks overall '
      'and return the JSON result with a 0-100 severity. Do not suggest any '
      'treatment or chemical.';

  static final Schema _schema = Schema.object(
    properties: {
      'is_berry_cluster': Schema.boolean(
        description:
            'True only if the image clearly shows a pepper berry spike.',
      ),
      'healthy': Schema.boolean(description: 'True if the spike looks clean.'),
      'problem_type': Schema.enumString(
        enumValues: _problemVocab,
        description: 'Best-matching label from the allowed list.',
      ),
      'severity_percentage': Schema.number(
        description:
            'Visual damage severity 0-100: how much of the spike looks '
            'affected overall. 0 when healthy.',
      ),
      'confidence': Schema.number(description: 'Confidence 0.0-1.0.'),
      'affected_regions': Schema.string(
        description: 'Short description of the damage seen.',
      ),
      'summary': Schema.string(
        description: 'One plain sentence for the farmer.',
      ),
    },
    requiredProperties: [
      'is_berry_cluster',
      'healthy',
      'problem_type',
      'severity_percentage',
      'confidence',
      'affected_regions',
      'summary',
    ],
  );
}
