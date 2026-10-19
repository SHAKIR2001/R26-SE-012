import 'dart:math';

enum HistoryFeature {
  gradingForecast('grading_forecast'),
  pestDetection('pest_detection'),
  leafDisease('leaf_disease'),
  berryDisease('berry_disease');

  const HistoryFeature(this.code);
  final String code;

  static HistoryFeature? tryParse(String? code) {
    for (final feature in values) {
      if (feature.code == code) return feature;
    }
    return null;
  }
}

enum HistoryAnalysisStage {
  detection('detection'),
  detailed('detailed');

  const HistoryAnalysisStage(this.code);
  final String code;

  static HistoryAnalysisStage parse(String? code) =>
      values.firstWhere((stage) => stage.code == code, orElse: () => detection);
}

class HistoryCursor {
  const HistoryCursor({required this.createdAtUtcMs, required this.id});

  final int createdAtUtcMs;
  final int id;
}

class HistoryPage {
  const HistoryPage({required this.records, required this.nextCursor});

  final List<HistoryRecord> records;
  final HistoryCursor? nextCursor;
}

class HistoryRecord {
  const HistoryRecord({
    required this.id,
    required this.recordKey,
    required this.feature,
    required this.createdAtUtcMs,
    required this.updatedAtUtcMs,
    required this.analysisStage,
    required this.outcomeCode,
    required this.primaryClassCode,
    required this.imageRelativePath,
    required this.imageMimeType,
    required this.imageByteLength,
    required this.resultSchemaVersion,
    required this.resultJson,
    required this.localeCode,
    required this.deletePending,
  });

  final int id;
  final String recordKey;
  final HistoryFeature feature;
  final int createdAtUtcMs;
  final int updatedAtUtcMs;
  final HistoryAnalysisStage analysisStage;
  final String outcomeCode;
  final String? primaryClassCode;
  final String imageRelativePath;
  final String imageMimeType;
  final int imageByteLength;
  final int resultSchemaVersion;
  final String resultJson;
  final String? localeCode;
  final bool deletePending;

  DateTime get createdAtLocal => DateTime.fromMillisecondsSinceEpoch(
    createdAtUtcMs,
    isUtc: true,
  ).toLocal();

  HistoryCursor get cursor =>
      HistoryCursor(createdAtUtcMs: createdAtUtcMs, id: id);

  factory HistoryRecord.fromMap(Map<String, Object?> map) {
    final feature = HistoryFeature.tryParse(map['feature_type'] as String?);
    if (feature == null) {
      throw const FormatException('Unsupported history feature type.');
    }
    return HistoryRecord(
      id: map['id'] as int,
      recordKey: map['record_key'] as String,
      feature: feature,
      createdAtUtcMs: map['created_at_utc_ms'] as int,
      updatedAtUtcMs: map['updated_at_utc_ms'] as int,
      analysisStage: HistoryAnalysisStage.parse(
        map['analysis_stage'] as String?,
      ),
      outcomeCode: map['outcome_code'] as String,
      primaryClassCode: map['primary_class_code'] as String?,
      imageRelativePath: map['image_relative_path'] as String,
      imageMimeType: map['image_mime_type'] as String,
      imageByteLength: map['image_byte_length'] as int,
      resultSchemaVersion: map['result_schema_version'] as int,
      resultJson: map['result_json'] as String,
      localeCode: map['locale_code'] as String?,
      deletePending: (map['delete_pending'] as int? ?? 0) != 0,
    );
  }
}

String newHistoryRecordKey() {
  final now = DateTime.now().toUtc().microsecondsSinceEpoch;
  final random = Random.secure().nextInt(0x7fffffff);
  return '${now.toRadixString(36)}-${random.toRadixString(36)}';
}
