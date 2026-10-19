import 'dart:convert';

import '../../../core/services/yolo_detector.dart';
import '../../../shared/models/detection.dart';
import '../../grading_forecast/models/grading_forecast_result.dart';
import '../../recommendations/berry_analysis.dart';
import '../../recommendations/leaf_analysis.dart';
import '../../recommendations/pest_analysis.dart';
import '../../recommendations/pest_treatment_engine.dart';
import '../../recommendations/remediation_engine.dart';

class HistoryPayloadCodec {
  HistoryPayloadCodec._();

  static const int schemaVersion = 1;

  static Map<String, dynamic>? tryDecode(String source) {
    try {
      final value = jsonDecode(source);
      if (value is! Map) return null;
      final map = value.map((key, item) => MapEntry(key.toString(), item));
      if (map['history_payload_version'] != schemaVersion) return null;
      return map;
    } catch (_) {
      return null;
    }
  }

  static String detection(DetectionResult result) => jsonEncode({
    'history_payload_version': schemaVersion,
    'kind': 'detection',
    'frame_width': result.frameSize.width,
    'frame_height': result.frameSize.height,
    'inference_ms': result.inferenceMs,
    'threshold_used': result.thresholdUsed,
    'low_confidence': result.lowConfidence,
    'detections': result.detections.map(_detection).toList(),
  });

  static String grading(GradingForecastResult result) => jsonEncode({
    'history_payload_version': schemaVersion,
    'kind': 'grading_forecast',
    'result': _grading(result),
  });

  static String leaf(LeafAnalysis analysis) => jsonEncode({
    'history_payload_version': schemaVersion,
    'kind': 'leaf_detail',
    'analysis': {
      'is_pepper_leaf': analysis.isPepperLeaf,
      'healthy': analysis.healthy,
      'disease_type': analysis.diseaseType,
      'severity_percentage': analysis.severityPercentage,
      'severity_band': analysis.severityBand,
      'confidence': analysis.confidence,
      'affected_regions': analysis.affectedRegions,
      'treatments': analysis.treatments,
      'summary': analysis.summary,
    },
  });

  static String pest(
    PestAnalysis analysis,
    PestTreatment treatment,
    Market market,
  ) => jsonEncode({
    'history_payload_version': schemaVersion,
    'kind': 'pest_detail',
    'market': market.name,
    'analysis': {
      'is_pepper_plant': analysis.isPepperPlant,
      'healthy': analysis.healthy,
      'pest_type': analysis.pestType,
      'plant_part': analysis.plantPart,
      'pest_count': analysis.pestCount,
      'severity_percentage': analysis.severityPercentage,
      'severity_band': analysis.severityBand,
      'confidence': analysis.confidence,
      'affected_regions': analysis.affectedRegions,
      'summary': analysis.summary,
    },
    'decision': _pestTreatment(treatment),
  });

  static String berry(
    BerryAnalysis analysis,
    Remediation remediation,
    Market market,
  ) => jsonEncode({
    'history_payload_version': schemaVersion,
    'kind': 'berry_detail',
    'market': market.name,
    'analysis': {
      'is_berry_cluster': analysis.isBerryCluster,
      'healthy': analysis.healthy,
      'problem_type': analysis.problemType,
      'severity_percentage': analysis.severityPercentage,
      'severity_band': analysis.severityBand,
      'confidence': analysis.confidence,
      'affected_regions': analysis.affectedRegions,
      'summary': analysis.summary,
    },
    'decision': _remediation(remediation),
  });

  static Map<String, dynamic> _detection(Detection detection) => {
    'class_id': detection.classId,
    'class_name': detection.className,
    'score': detection.score,
    'left': detection.rect.left,
    'top': detection.rect.top,
    'right': detection.rect.right,
    'bottom': detection.rect.bottom,
  };

  static Map<String, dynamic> _grading(GradingForecastResult result) => {
    'schema_version': result.schemaVersion,
    'grading': {
      'status': result.grading.status,
      'decision': result.grading.decision,
      'grade': result.grading.grade,
      'model_confidence': result.grading.modelConfidence,
      'detection_confidence': result.grading.detectionConfidence,
      'class_margin': result.grading.classMargin,
      'quality_status': result.grading.qualityStatus,
      'rejection_reason': result.grading.rejectionReason,
      'confidence_interpretation': result.grading.confidenceInterpretation,
    },
    'market': {
      'status': result.market.status,
      'source': result.market.source,
      'price_grade': result.market.priceGrade,
      'latest_reference_date': result.market.latestReferenceDate,
      'latest_reference_price': result.market.latestReferencePrice,
      'forecast_target_date': result.market.forecastTargetDate,
      'forecast_return': result.market.forecastReturn,
      'forecast_price': result.market.forecastPrice,
      'forecast_direction': result.market.forecastDirection,
      'forecast_interval': result.market.forecastInterval == null
          ? null
          : {
              'lower': result.market.forecastInterval!.lower,
              'upper': result.market.forecastInterval!.upper,
              'label': result.market.forecastInterval!.label,
            },
      'persistence_price': result.market.persistencePrice,
      'model_vs_persistence': result.market.modelVsPersistence,
      'forecast_signal': result.market.forecastSignal,
      'evidence_partition': result.market.evidencePartition,
    },
    'decision_support': {
      'category': result.decisionSupport.category,
      'summary': result.decisionSupport.summary,
      'limitations': result.decisionSupport.limitations,
    },
    'trace': result.trace,
    'runtime': {
      'grading': result.runtime.grading,
      'price': result.runtime.price,
      'mobile': result.runtime.mobile,
      'tflite': result.runtime.tflite,
    },
  };

  static Map<String, dynamic> _option(TreatmentOption option) => {
    'name': option.name,
    'mix': option.mix,
    'method': option.method,
    'allowed_in_market': option.allowedInMarket,
    'restriction': option.restriction,
    'phi': option.phi,
    'is_chemical': option.isChemical,
  };

  static Map<String, dynamic> _pestTreatment(PestTreatment treatment) => {
    'action': treatment.action,
    'above_threshold': treatment.aboveThreshold,
    'options': treatment.options.map(_option).toList(),
    'warnings': treatment.warnings,
    'note': treatment.note,
  };

  static Map<String, dynamic> _remediation(Remediation remediation) => {
    'action': remediation.action,
    'options': remediation.options.map(_option).toList(),
    'warnings': remediation.warnings,
    'export_note': remediation.exportNote,
  };
}
