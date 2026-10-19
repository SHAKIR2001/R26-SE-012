import 'dart:typed_data';
import '../models/grading_forecast_result.dart';
import 'grading_forecast_api_service.dart';

/// Feature-level façade used by the screens.
///
/// Keeping this boundary separate makes the UI independent of HTTP details
/// and leaves room for controlled service substitution in tests without
/// introducing a competing local grading implementation.
class GradingForecastAnalysisService {
  GradingForecastAnalysisService({GradingForecastApiService? apiService})
    : _apiService = apiService ?? GradingForecastApiService();
  final GradingForecastApiService _apiService;
  // Phase 7 intentionally has no offline grading result path.
  bool get isOffline => false;
  Future<GradingForecastResult> analyzeBytes(
    Uint8List bytes,
    String filename,
  ) => _apiService.analyzeBytes(bytes, filename);
  Future<void> dispose() async => _apiService.close();
}
