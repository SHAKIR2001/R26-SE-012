import 'package:flutter/foundation.dart';

import '../../l10n/app_localizations.dart';
import 'ai_leaf_service.dart' show LeafAnalysisException;

/// Logs the real, detailed error for developers only (console / logcat). This
/// is where the actual provider message, status code and stack trace go — never
/// the user-facing UI.
void logAiError(String where, Object error, [StackTrace? stack]) {
  debugPrint('[AI][$where] $error');
  if (stack != null) debugPrint('[AI][$where] $stack');
}

/// Maps any AI/analysis error to a short, friendly, user-safe message. Never
/// leaks stack traces, provider names (Gemini/Claude), status codes or raw
/// server payloads to the client.
String friendlyAiMessage(Object error, AppLocalizations t) {
  final raw =
      (error is LeafAnalysisException ? error.message : error.toString())
          .toLowerCase();

  // Developer setup problem (missing/invalid key).
  if (raw.contains('api key') ||
      raw.contains('no ai key') ||
      raw.contains('unauthorized') ||
      raw.contains('permission') ||
      raw.contains('401') ||
      raw.contains('403')) {
    return t.errSetup;
  }
  // Offline / no network.
  if (raw.contains('socketexception') ||
      raw.contains('failed host lookup') ||
      raw.contains('network is unreachable') ||
      raw.contains('no address associated') ||
      raw.contains('network') ||
      raw.contains('connection')) {
    return t.errOffline;
  }
  // Service busy / overloaded / timed out (503, UNAVAILABLE, deadline, 429).
  if (raw.contains('503') ||
      raw.contains('unavailable') ||
      raw.contains('deadline') ||
      raw.contains('overloaded') ||
      raw.contains('timeout') ||
      raw.contains('timed out') ||
      raw.contains('429') ||
      raw.contains('rate limit') ||
      raw.contains('500') ||
      raw.contains('502')) {
    return t.errBusy;
  }
  // Photo couldn't be read.
  if (raw.contains('could not read') ||
      raw.contains('could not decode') ||
      raw.contains('decode')) {
    return t.couldNotReadImage;
  }
  // Anything else.
  return t.errGeneric;
}
