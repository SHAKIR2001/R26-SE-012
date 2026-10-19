import '../l10n/app_localizations.dart';

/// Translates a predicted class label (from the on-device detector, the AI
/// detector, or an analysis service's enum vocabulary) into the active language.
///
/// The vocabulary is a fixed, known set, so we map it explicitly. Scientific
/// pest names (e.g. "Diconocoris distanti") and any free-form/unknown label fall
/// through unchanged — scientific binomials are the same in every language.
String localizedClassName(String raw, AppLocalizations t) {
  final key = raw.trim().toLowerCase().replaceAll('_', ' ');
  switch (key) {
    case 'healthy':
    case 'healthy leaf':
      return t.clsHealthy;
    case 'healthy leaves':
      return t.clsHealthyLeaves;
    case 'healthy berry':
    case 'healthy_berry':
      return t.clsHealthyBerry;
    case 'leaf blight':
      return t.clsLeafBlight;
    case 'little leaf':
      return t.clsLittleLeaf;
    case 'quick wilt':
      return t.clsQuickWilt;
    case 'lace bug damage':
    case 'lace_bug_damage':
      return t.clsLaceBugDamage;
    case 'nutrient deficiency':
      return t.clsNutrientDeficiency;
    case 'other disease':
      return t.clsOtherDisease;
    case 'other damage':
      return t.clsOtherDamage;
    case 'uncertain':
      return t.clsUncertain;
    default:
      return raw;
  }
}
