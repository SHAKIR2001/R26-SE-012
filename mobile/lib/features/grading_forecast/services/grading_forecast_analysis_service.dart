// =============================================================================
// File: grading_forecast_analysis_service.dart
// Purpose: Provides the grading forecast analysis service application service.
// =============================================================================
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
  // Analyze the supplied image bytes.
  Future<GradingForecastResult> analyzeBytes(
    Uint8List bytes,
    String filename,
  ) {
    // Forward the image data to the API client for upload to the backend.
    return _apiService.analyzeBytes(bytes, filename);
  }
  // Release controllers, listeners, and other owned resources.
  Future<void> dispose() async => _apiService.close();
}
