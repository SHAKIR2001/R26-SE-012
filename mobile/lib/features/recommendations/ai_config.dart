/// AI API configuration.
///
/// Keys are supplied at build/run time from the project .env so they are never
/// committed:
///   flutter run --dart-define-from-file=/path/to/mobile/.env
///
/// The .env must contain:
///   GEMINI_API_KEY=your_gemini_key      # detector + fallback classifier
///   ANTHROPIC_API_KEY=your_claude_key   # primary crop classifier (optional)
///
/// Gemini key: https://aistudio.google.com/app/apikey
/// Claude key: https://platform.claude.com/settings/keys
class AiConfig {
  static const String apiKey = String.fromEnvironment('GEMINI_API_KEY');

  /// Latest stable multimodal model — strong fine-grained classification and
  /// bounding boxes. If a pinned version is ever unavailable, 'gemini-flash-latest'
  /// is a safe auto-updating fallback.
  static const String model = 'gemini-3.6-flash';

  static bool get hasKey => apiKey.isNotEmpty;

  // ---- Claude (two-stage classifier) ----
  // Gemini detects + boxes every object; Claude re-classifies each crop for
  // higher fine-grained accuracy. If this key is absent the app transparently
  // uses Gemini's own labels, so Claude is a pure accuracy upgrade, never a
  // hard dependency.
  static const String claudeApiKey = String.fromEnvironment(
    'ANTHROPIC_API_KEY',
  );

  // Opus for the crop classifier: the Leaf Blight vs Quick Wilt call is a hard
  // fine-grained visual discrimination, and Opus is the most accurate at it.
  // MUST run with NO `thinking` param (budgetTokens:/enabled 400s on this model —
  // see claude_classifier_service). Switch to 'claude-sonnet-5-5' (also valid
  // with no thinking) if you want it cheaper/faster.
  static const String claudeModel = 'claude-opus-5-5';

  static bool get hasClaudeKey => claudeApiKey.isNotEmpty;
}
