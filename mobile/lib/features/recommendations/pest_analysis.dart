/// Vision result of an AI pest analysis on a pepper-plant photo.
///
/// AI identifies and counts what it can see; it does NOT recommend any
/// pesticide — the [PestTreatmentEngine] owns treatment so an LLM can't suggest
/// an export-banned chemical or advise spraying below the economic threshold.
class PestAnalysis {
  /// False when the image isn't a pepper plant part → ask for a retake.
  final bool isPepperPlant;

  /// True when no pest / damage is present.
  final bool healthy;

  /// e.g. "Gynaikothrips karny", "Diconocoris distanti", "Other pest".
  final String pestType;

  /// leaf | stem | berry | unknown — pests differ by location.
  final String plantPart;

  /// Estimated pests visible in the frame.
  final int pestCount;

  /// Overall infestation severity, 0–100 (visual estimate incl. damage).
  final double severityPercentage;

  final double confidence;
  final String affectedRegions;
  final String summary;

  /// True when the detail analysis could not confirm a pest identity. This is
  /// a fail-closed result: the UI asks for a clearer image and the treatment
  /// engine must not recommend chemicals.
  bool get isUncertain => pestType.trim().toLowerCase() == 'uncertain';

  /// Creates a new pest analysis result.
  const PestAnalysis({
    required this.isPepperPlant,
    required this.healthy,
    required this.pestType,
    required this.plantPart,
    required this.pestCount,
    required this.severityPercentage,
    required this.confidence,
    required this.affectedRegions,
    required this.summary,
  });

  /// none | mild | moderate | severe.
  String get severityBand {
    if (healthy || severityPercentage <= 0) return 'none';
    if (severityPercentage <= 20) return 'mild';
    if (severityPercentage <= 50) return 'moderate';
    return 'severe';
  }

  /// Creates a [PestAnalysis] object from JSON data.
  ///
  /// This is normally used to convert the response received
  /// from the AI backend/API into a Dart object that can be used
  /// throughout the Flutter application.
  factory PestAnalysis.fromJson(Map<String, dynamic> j) {
    double asDouble(Object? v) =>
        v is num ? v.toDouble() : (double.tryParse('${v ?? ''}') ?? 0);
    int asInt(Object? v) =>
        v is num ? v.round() : (int.tryParse('${v ?? ''}') ?? 0);

    // Convert the JSON response into a PestAnalysis object.
    return PestAnalysis(
      isPepperPlant: j['is_pepper_plant'] == true,

      // Checks whether the plant was classified as healthy.
      healthy: j['healthy'] == true,
      pestType: (j['pest_type'] ?? 'Uncertain').toString(),
      plantPart: (j['plant_part'] ?? 'unknown').toString(),
      pestCount: asInt(j['pest_count']),
      severityPercentage: asDouble(j['severity_percentage']),
      confidence: asDouble(j['confidence']),
      affectedRegions: (j['affected_regions'] ?? '').toString(),
      summary: (j['summary'] ?? '').toString(),
    );
  }
}
