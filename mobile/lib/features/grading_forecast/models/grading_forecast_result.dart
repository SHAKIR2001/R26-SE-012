/// Typed representation of the Phase 6 decision-support response consumed by
/// the Flutter presentation layer.
///
/// The app parses the complete contract before rendering anything. This keeps
/// research/trace fields available for debugging while allowing the farmer UI
/// to show only the appropriate grade, rejection, or price-outlook message.
class GradingForecastResult {
  const GradingForecastResult({
    required this.schemaVersion,
    required this.grading,
    required this.market,
    required this.decisionSupport,
    required this.trace,
    required this.runtime,
  });
  final String schemaVersion;
  final GradingResult grading;
  final MarketResult market;
  final DecisionSupportResult decisionSupport;
  final Map<String, dynamic> trace;
  final RuntimeResult runtime;
  factory GradingForecastResult.fromJson(Map<String, dynamic> json) {
    // A schema version prevents a newer or unrelated backend response from
    // being interpreted as a valid Phase 7 result by an older app build.
    final schemaVersion = _requiredString(json['schema_version'], 'schema_version');
    if (schemaVersion != 'phase6_decision_support_v1') {
      throw const FormatException('Unsupported decision-support schema.');
    }
    final result = GradingForecastResult(
      schemaVersion: schemaVersion,
      grading: GradingResult.fromJson(_requiredMap(json['grading'], 'grading')),
      market: MarketResult.fromJson(_requiredMap(json['market'], 'market')),
      decisionSupport: DecisionSupportResult.fromJson(
        _requiredMap(json['decision_support'], 'decision_support'),
      ),
      trace: _requiredMap(json['trace'], 'trace'),
      runtime: RuntimeResult.fromJson(_requiredMap(json['runtime'], 'runtime')),
    );
    _validateDecisionContract(result);
    return result;
  }
}

/// Grading-stage output. A non-accepted status must not be priced.
class GradingResult {
  const GradingResult({
    required this.status,
    required this.decision,
    this.grade,
    this.modelConfidence,
    this.detectionConfidence,
    this.classMargin,
    required this.qualityStatus,
    this.rejectionReason,
    required this.confidenceInterpretation,
  });
  final String status;
  final String decision;
  final String? grade;
  final double? modelConfidence;
  final double? detectionConfidence;
  final double? classMargin;
  final String qualityStatus;
  final String? rejectionReason;
  final String confidenceInterpretation;
  bool get isAccepted => status == 'ACCEPTED';
  factory GradingResult.fromJson(Map<String, dynamic> json) => GradingResult(
    status: _requiredString(json['status'], 'grading.status'),
    decision: _requiredString(json['decision'], 'grading.decision'),
    grade: _nullableString(json['grade']),
    modelConfidence: _nullableDouble(json['model_confidence']),
    detectionConfidence: _nullableDouble(json['detection_confidence']),
    classMargin: _nullableDouble(json['class_margin']),
    qualityStatus: _requiredString(json['quality_status'], 'grading.quality_status'),
    rejectionReason: _nullableString(json['rejection_reason']),
    confidenceInterpretation: _requiredString(
      json['confidence_interpretation'],
      'grading.confidence_interpretation',
    ),
  );
}

/// Diagnostic forecast range supplied by the frozen price evidence.
/// It is not presented as a calibrated probability interval.
class ForecastInterval {
  const ForecastInterval({
    required this.lower,
    required this.upper,
    required this.label,
  });
  final double lower;
  final double upper;
  final String label;
  factory ForecastInterval.fromJson(Map<String, dynamic> json) =>
      ForecastInterval(
        lower: _double(json['lower']),
        upper: _double(json['upper']),
        label: _string(json['label']),
      );
}

/// Grade-specific reference-price and forecast evidence.
///
/// `priceGrade` is validated against the grading result below; the client
/// never swaps Grade 1 and Grade 2 evidence or invents a fallback price.
class MarketResult {
  const MarketResult({
    required this.status,
    this.source,
    this.priceGrade,
    this.latestReferenceDate,
    this.latestReferencePrice,
    this.forecastTargetDate,
    this.forecastReturn,
    this.forecastPrice,
    this.forecastDirection,
    this.forecastInterval,
    this.persistencePrice,
    this.modelVsPersistence,
    this.forecastSignal,
    this.evidencePartition,
  });
  final String status;
  final String? source;
  final String? priceGrade;
  final String? latestReferenceDate;
  final double? latestReferencePrice;
  final String? forecastTargetDate;
  final double? forecastReturn;
  final double? forecastPrice;
  final String? forecastDirection;
  final ForecastInterval? forecastInterval;
  final double? persistencePrice;
  final String? modelVsPersistence;
  final String? forecastSignal;
  final String? evidencePartition;
  bool get isAvailable => status == 'AVAILABLE';
  factory MarketResult.fromJson(Map<String, dynamic> json) => MarketResult(
    status: _requiredString(json['status'], 'market.status'),
    source: _nullableString(json['source']),
    priceGrade: _nullableString(json['price_grade']),
    latestReferenceDate: _nullableString(json['latest_reference_date']),
    latestReferencePrice: _nullableDouble(json['latest_reference_price']),
    forecastTargetDate: _nullableString(json['forecast_target_date']),
    forecastReturn: _nullableDouble(json['forecast_return']),
    forecastPrice: _nullableDouble(json['forecast_price']),
    forecastDirection: _nullableString(json['forecast_direction']),
    forecastInterval: json['forecast_interval'] == null
        ? null
        : ForecastInterval.fromJson(
            _requiredMap(json['forecast_interval'], 'market.forecast_interval'),
          ),
    persistencePrice: _nullableDouble(json['persistence_price']),
    modelVsPersistence: _nullableString(json['model_vs_persistence']),
    forecastSignal: _nullableString(json['forecast_signal']),
    evidencePartition: _nullableString(json['evidence_partition']),
  );
}

/// Phase 6 category and explanation selected by the authoritative engine.
class DecisionSupportResult {
  const DecisionSupportResult({
    required this.category,
    required this.summary,
    required this.limitations,
  });
  final String category;
  final String summary;
  final List<String> limitations;
  factory DecisionSupportResult.fromJson(Map<String, dynamic> json) =>
      DecisionSupportResult(
        category: _requiredString(json['category'], 'decision_support.category'),
        summary: _requiredString(json['summary'], 'decision_support.summary'),
        limitations: _strings(json['limitations']),
      );
}

/// Provenance/runtime labels returned for research diagnostics.
/// These values are intentionally not used to create a new prediction.
class RuntimeResult {
  const RuntimeResult({
    required this.grading,
    required this.price,
    required this.mobile,
    required this.tflite,
  });
  final String grading;
  final String price;
  final String mobile;
  final String tflite;
  factory RuntimeResult.fromJson(Map<String, dynamic> json) => RuntimeResult(
    grading: _requiredString(json['grading'], 'runtime.grading'),
    price: _requiredString(json['price'], 'runtime.price'),
    mobile: _requiredString(json['mobile'], 'runtime.mobile'),
    tflite: _requiredString(json['tflite'], 'runtime.tflite'),
  );
}

void _validateDecisionContract(GradingForecastResult result) {
  // Keep this validation fail-closed. A malformed response must not become a
  // plausible-looking grade or market recommendation in the mobile UI.
  const statuses = {'ACCEPTED', 'REJECTED', 'UNCERTAIN'};
  const categories = {
    'REJECT',
    'UNCERTAIN_GRADE',
    'CONFLICTING_SAMPLE_VIEWS',
    'PRICE_DATA_UNAVAILABLE',
    'FORECAST_UNAVAILABLE',
    'UPWARD_PRICE_OUTLOOK',
    'DOWNWARD_PRICE_OUTLOOK',
    'FLAT_PRICE_OUTLOOK',
    'HIGH_UNCERTAINTY_OUTLOOK',
  };
  if (!statuses.contains(result.grading.status) ||
      !categories.contains(result.decisionSupport.category)) {
    throw const FormatException('Backend returned an unknown decision state.');
  }

  final nonAccepted = result.grading.status != 'ACCEPTED';
  // Rejected and uncertain samples stop before pricing. The backend contract
  // must therefore contain no market output for either state.
  if (nonAccepted &&
      (result.market.isAvailable ||
          result.market.priceGrade != null ||
          result.market.latestReferencePrice != null ||
          result.market.forecastPrice != null)) {
    throw const FormatException(
      'Rejected or uncertain grading included market output.',
    );
  }
  if (result.grading.status == 'REJECTED' &&
      result.decisionSupport.category != 'REJECT') {
    throw const FormatException('Rejected grading has an invalid category.');
  }
  if (result.grading.status == 'UNCERTAIN' &&
      result.decisionSupport.category != 'UNCERTAIN_GRADE' &&
      result.decisionSupport.category != 'CONFLICTING_SAMPLE_VIEWS') {
    throw const FormatException('Uncertain grading has an invalid category.');
  }
  if (result.market.isAvailable) {
    // Price evidence is routed strictly by the project V3 grade. Grade 1 and
    // Grade 2 are never averaged, discounted, or used interchangeably.
    final expectedPriceGrade = switch (result.grading.grade) {
      'V3 Grade 1' => 'Grade 1',
      'V3 Grade 2' => 'Grade 2',
      _ => null,
    };
    if (result.grading.status != 'ACCEPTED' ||
        expectedPriceGrade == null ||
        result.market.priceGrade != expectedPriceGrade ||
        result.market.latestReferencePrice == null ||
        result.market.forecastPrice == null) {
      throw const FormatException(
        'Backend returned an invalid grade-price route.',
      );
    }
  }
}

String _string(Object? value) => value?.toString() ?? '';
String _requiredString(Object? value, String field) {
  if (value is! String || value.trim().isEmpty) {
    throw FormatException('Missing or invalid $field.');
  }
  return value;
}

Map<String, dynamic> _requiredMap(Object? value, String field) {
  if (value is! Map) throw FormatException('Missing or invalid $field.');
  return value.map((key, item) => MapEntry(key.toString(), item));
}

String? _nullableString(Object? value) => value?.toString();
double _double(Object? value) {
  final parsed = value is num
      ? value.toDouble()
      : double.tryParse(value?.toString() ?? '');
  if (parsed == null || !parsed.isFinite) {
    throw const FormatException('Missing or invalid numeric value.');
  }
  return parsed;
}

double? _nullableDouble(Object? value) => value == null ? null : _double(value);
List<String> _strings(Object? value) {
  if (value is! List) {
    throw const FormatException('Missing or invalid string list.');
  }
  return value.map((item) => item.toString()).toList();
}
