import 'package:flutter_test/flutter_test.dart';
import 'package:pepper_care/features/grading_forecast/models/grading_forecast_result.dart';

void main() {
  test('parses the Phase 6 compatible accepted response', () {
    final result = GradingForecastResult.fromJson({
      'schema_version': 'phase6_decision_support_v1',
      'grading': {
        'status': 'ACCEPTED',
        'decision': 'GRADE_1',
        'grade': 'V3 Grade 1',
        'model_confidence': 0.91,
        'detection_confidence': 0.91,
        'class_margin': 0.8,
        'quality_status': 'PASSED',
        'rejection_reason': null,
        'confidence_interpretation':
            'model score; not a calibrated probability',
      },
      'market': {
        'status': 'AVAILABLE',
        'source': 'EAC farm-gate reference price',
        'price_grade': 'Grade 1',
        'latest_reference_date': '2026-09-15',
        'latest_reference_price': 1987.5,
        'forecast_target_date': '2026-09-29',
        'forecast_price': 1990.6,
        'forecast_return': 0.0015,
        'forecast_direction': 'UP',
        'forecast_signal': 'HIGH_UNCERTAINTY',
        'forecast_interval': {
          'lower': 1942.49,
          'upper': 2038.70,
          'label': 'validation-derived forecast interval',
        },
      },
      'decision_support': {
        'category': 'HIGH_UNCERTAINTY_OUTLOOK',
        'summary': 'Limited research outlook.',
        'limitations': ['research only'],
      },
      'trace': {'grading_model_sha256': 'abc'},
      'runtime': {
        'grading': 'ONNX_RUNTIME_CPU',
        'price': 'FROZEN_PHASE5_FORECAST_RECORD',
        'mobile': 'BACKEND_API',
        'tflite': 'NOT_IMPLEMENTED_OR_CLAIMED',
      },
    });
    expect(result.grading.grade, 'V3 Grade 1');
    expect(result.market.priceGrade, 'Grade 1');
    expect(result.market.isAvailable, isTrue);
    expect(result.decisionSupport.category, 'HIGH_UNCERTAINTY_OUTLOOK');
  });

  test('parses rejection without fabricated market values', () {
    final result = GradingForecastResult.fromJson({
      'schema_version': 'phase6_decision_support_v1',
      'grading': {
        'status': 'REJECTED',
        'decision': 'NO_PEPPER',
        'quality_status': 'NOT_APPLICABLE',
        'confidence_interpretation':
            'model score; not a calibrated probability',
      },
      'market': {'status': 'NOT_AVAILABLE_REJECTED_INPUT'},
      'decision_support': {
        'category': 'REJECT',
        'summary': 'No market outlook.',
        'limitations': <String>[],
      },
      'trace': <String, dynamic>{},
      'runtime': {
        'grading': 'ONNX_RUNTIME_CPU',
        'price': 'FROZEN_PHASE5_FORECAST_RECORD',
        'mobile': 'BACKEND_API',
        'tflite': 'NOT_IMPLEMENTED_OR_CLAIMED',
      },
    });
    expect(result.market.isAvailable, isFalse);
    expect(result.market.forecastPrice, isNull);
  });

  test('rejects uncertainty response that leaks market output', () {
    expect(
      () => GradingForecastResult.fromJson({
        'schema_version': 'phase6_decision_support_v1',
        'grading': {
          'status': 'UNCERTAIN',
          'decision': 'UNCERTAIN_GRADE',
          'quality_status': 'PASSED',
          'confidence_interpretation':
              'model score; not a calibrated probability',
        },
        'market': {
          'status': 'AVAILABLE',
          'price_grade': 'Grade 2',
          'latest_reference_price': 1940.0,
          'forecast_price': 1931.13,
        },
        'decision_support': {
          'category': 'UNCERTAIN_GRADE',
          'summary': 'No reliable grade.',
          'limitations': <String>[],
        },
        'trace': <String, dynamic>{},
        'runtime': {
          'grading': 'ONNX_RUNTIME_CPU',
          'price': 'FROZEN_PHASE5_FORECAST_RECORD',
          'mobile': 'BACKEND_API',
          'tflite': 'NOT_IMPLEMENTED_OR_CLAIMED',
        },
      }),
      throwsFormatException,
    );
  });

  test('rejects unsupported response schema', () {
    expect(
      () => GradingForecastResult.fromJson({
        'schema_version': 'unknown',
      }),
      throwsFormatException,
    );
  });
}
